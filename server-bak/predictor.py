import json
import logging
import tensorflow as tf
from tensorflow import keras

import cache
import config
import ee_landsat

tf.enable_eager_execution()


def make_dataset(filenames, batch_size=64):
  # The features_dict is like a schema for the TensorFlow Example protos.
  image_size = config.tile_size + 2*config.cnn_padding
  features_dict = {
      name: tf.FixedLenFeature(
          shape=[image_size, image_size], dtype=tf.float32)
      for name in config.features
  }

  # Create a TFRecordDataset with all the files and apply the parsing function.
  dataset = (
      tf.data.TFRecordDataset(filenames, compression_type='GZIP')
      .map(
          lambda example: tf.parse_single_example(example, features_dict),
          num_parallel_calls=config.dataset_num_parallel_calls,
      )
  )

  # Get the input feature vectors.
  def get_feature_vectors(features_dict):
    features_vec = [features_dict[name] for name in config.features]
    # (bands, x, y) -> (x, y, bands)
    features_vec = tf.transpose(features_vec, [1, 2, 0])
    return (features_vec, )
  dataset = dataset.map(get_feature_vectors)

  # Batch the elements.
  dataset = dataset.batch(batch_size)
  dataset = dataset.prefetch(1)
  return dataset


keras_model = None


def predict(block_id, inputs_file, mixer_file, predictions_file):
  result = {
      'id': block_id,
      'predictions_file': predictions_file,
      'mixer_file': mixer_file,
  }
  if cache.gcs_file_exists(predictions_file):
    logging.info('{}: predictions found {}'.format(block_id, predictions_file))
    return result

  global keras_model
  if keras_model is None:
    keras_model = keras.models.load_model(config.model_file)

  with tf.gfile.Open(mixer_file) as f:
    mixer = json.load(f)
    cols = int(mixer['patchesPerRow'])
    rows = int(mixer['totalPatches'] / cols)

  logging.info('{}: predictions running ({}x{})'.format(block_id, cols, rows))
  padding = config.cnn_padding
  with tf.io.TFRecordWriter(predictions_file) as f:
    dataset = make_dataset(inputs_file, batch_size=cols)
    for i, padded_patch in enumerate(keras_model.predict(dataset, steps=rows)):
      logging.info('{}: prediction patch {} of {}'.format(block_id, i+1, rows))
      patch = padded_patch[padding:-padding, padding:-padding, :]
      patch_indices = tf.reshape(
          tf.argmax(patch, axis=2),
          shape=[config.tile_size * config.tile_size],
      )

      example = tf.train.Example(features=tf.train.Features(feature={
          'landcover': tf.train.Feature(
              int64_list=tf.train.Int64List(value=patch_indices)
          ),
      }))
      f.write(example.SerializeToString())
  return result
