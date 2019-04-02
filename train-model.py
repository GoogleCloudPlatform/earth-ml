import argparse
import ee
import os
import tensorflow as tf
from tensorflow import keras

import landsat
from classifier import config

tf.enable_eager_execution()


def extract_data(bucket, max_data_points=None):
  # Get the neighboring patch for every feature.
  def get_neighboring_patch(feature):
    # Get the start and end date from the date the feature was collected.
    date = ee.String(feature.get('image')).split('_').get(-1)
    year = ee.Number.parse(ee.String(date).slice(0, 4))
    month = ee.Number.parse(ee.String(date).slice(4, 6))
    day = ee.Number.parse(ee.String(date).slice(6, 8))

    # Get the image that matches where/when the point was extracted.
    image = landsat.get_image(year)

    # Set the label property to the expected name.
    feature = feature.set({config.label: feature.get('level1')})

    # Set the shard index from an initial random number from 0 to 1.
    feature = feature.set({'shard': (
        ee.Number(feature.get('shard'))
        .multiply(config.train_and_test_files)
        .toInt()
    )})

    # Return the feature as a feature collection of 1 element.
    return ee.FeatureCollection([
        image
        .neighborhoodToArray(ee.Kernel.square(config.cnn_padding))
        .sampleRegions(
            collection=ee.FeatureCollection([feature]),
            scale=30,
        )
        .first()
    ])

  # Get a patch of pixels for every data point in the Gong dataset.
  dataset = (
      ee.FeatureCollection('ft:1Olr1sJoEBs9mznunucZxk8M2a1Si8eMapOERn92K')
      .randomColumn('shard', 42)
      .map(get_neighboring_patch)
      .flatten()
  )

  if max_data_points is not None:
    dataset = dataset.limit(max_data_points)

  # Shard and write all the data points.
  print("Creating tasks...")
  tasks = [
      ee.batch.Export.table.toCloudStorage(
          collection=dataset.filter(ee.Filter.eq('shard', shard)),
          description=f"gong {shard+1} of {config.train_and_test_files}",
          bucket=bucket,
          fileNamePrefix=f"data/train/{shard}_",
          selectors=config.features + [config.label],
          fileFormat='TFRecord',
      )
      for shard in range(config.train_and_test_files)
  ]
  print(f"Starting {len(tasks)} tasks")
  for task in tasks:
    task.start()

  for task in tasks:
    print(f"Waiting for {task.config['description']} ({task.id})")
    landsat.wait_for_task(task.id)


def make_dataset(filenames, batch_size, shuffle):
  # The features_dict is like a schema for the tf.Example protos.
  features_dict = {
      name: tf.FixedLenFeature(
          shape=[config.cnn_patch_size, config.cnn_patch_size], dtype=tf.float32)
      for name in config.features
  }
  features_dict[config.label] = tf.FixedLenFeature(
      shape=[1, 1], dtype=tf.float32)

  # Create a TFRecordDataset with all the files and apply the parsing function.
  dataset = (
      tf.data.TFRecordDataset(filenames, compression_type='GZIP')
      .map(
          lambda example: tf.parse_single_example(example, features_dict),
          num_parallel_calls=config.dataset_num_parallel_calls,
      )
  )

  # Get the input feature vectors and label vector.
  def get_feature_and_label_vectors(features_dict):
    label_value = tf.cast(features_dict.pop(config.label), tf.int32)
    label_vec = tf.one_hot(label_value, len(config.classifications))
    features_vec = [features_dict[name] for name in config.features]
    # (bands, x, y) -> (x, y, bands)
    features_vec = tf.transpose(features_vec, [1, 2, 0])
    return features_vec, label_vec
  dataset = dataset.map(get_feature_and_label_vectors)

  # Shuffle, repeat, and batch the elements.
  if shuffle:
    dataset = dataset.apply(
        tf.data.experimental.shuffle_and_repeat(batch_size * 16))
  else:
    dataset = dataset.repeat()
  dataset = dataset.batch(batch_size)
  dataset = dataset.prefetch(1)
  return dataset


def train_files(bucket):
  return [
      f"gs://{bucket}/data/train/{shard}_ee_export.tfrecord.gz"
      for shard in range(config.train_files)
  ]


def test_files(bucket):
  return [
      f"gs://{bucket}/data/train/{shard}_ee_export.tfrecord.gz"
      for shard in range(config.train_files, config.train_and_test_files)
  ]


def train_dataset(bucket, batch_size=512, shuffle=True):
  return make_dataset(train_files(bucket), batch_size, shuffle)


def test_dataset(bucket, batch_size=128, shuffle=False):
  return make_dataset(train_files(bucket), batch_size, shuffle)


def make_model():
  model = keras.models.Sequential([
      keras.layers.Conv2D(
          name='image',
          input_shape=(None, None, len(config.features)),
          filters=32,
          kernel_size=config.cnn_patch_size,
          activation='relu',
      ),
      keras.layers.Conv2DTranspose(
          name='output',
          filters=len(config.classifications),
          kernel_size=config.cnn_patch_size,
          activation='softmax',
      ),
  ])

  model.compile(
      # optimizer=keras.optimizers.Adam(),
      optimizer=tf.train.AdamOptimizer(),
      loss='categorical_crossentropy',
      metrics=['categorical_accuracy'],
  )

  return model


def run(
    bucket,
    train_epochs,
    train_batches_per_epoch,
    test_batches,
    max_train_data_points=None,
    force_data_extract=False,
):
  should_extract_data = args.force_data_extract
  for filename in test_files(args.bucket) + train_files(args.bucket):
    if not tf.gfile.Exists(filename):
      print(filename)
      should_extract_data = True
      break

  if should_extract_data:
    extract_data(args.bucket, args.max_train_data_points)

  model = make_model()
  print(model.summary())

  print('Training model')
  model.fit(
      train_dataset(bucket),
      epochs=train_epochs,
      steps_per_epoch=train_batches_per_epoch,
      validation_data=test_dataset(bucket),
      validation_steps=test_batches,
  )

  print(f"Saving model to {config.model_file}")
  keras.models.save_model(model, config.model_file)


if __name__ == '__main__':
  parser = argparse.ArgumentParser()
  parser.add_argument(
      '--bucket',
      type=str,
      required=True,
  )
  parser.add_argument(
      '--train-epochs',
      type=int,
      default=10,
  )
  parser.add_argument(
      '--train-batches-per-epoch',
      type=int,
      default=30,
  )
  parser.add_argument(
      '--test-batches',
      type=int,
      default=5,
  )
  parser.add_argument(
      '--max-train-data-points',
      type=int,
      default=None,
  )
  parser.add_argument(
      '--force-data-extract',
      type=bool,
      default=False,
  )
  args = parser.parse_args()

  run(
      args.bucket,
      args.train_epochs,
      args.train_batches_per_epoch,
      args.test_batches,
      args.max_train_data_points,
      args.force_data_extract,
  )
