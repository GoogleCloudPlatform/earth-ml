import json
import logging
import os
from google.cloud import pubsub
from google.cloud import storage

import tensorflow as tf
tf.enable_eager_execution()

PROJECT = os.environ['PROJECT']
ML_ENGINE_TOPIC = os.environ['ML_ENGINE_TOPIC']

subscriber = pubsub.SubscriberClient()
storage_client = storage.Client()


def run(ml_engine_file=None):
  if ml_engine_file:
    logging.info('Running for file: ' + ml_engine_file)
    json2tfrecord(ml_engine_file)
  else:
    logging.info("Listening...")
    future = subscriber.subscribe(
        subscription=subscriber.subscription_path(PROJECT, ML_ENGINE_TOPIC),
        callback=ml_engine_callback,
    )
    future.result()


def ml_engine_callback(message):
  message.ack()
  json2tfrecord(message.data.decode('utf-8'))


def json2tfrecord(ml_engine_file):
  logging.info('ml_engine_file: ' + ml_engine_file)

  # gs://<bucket>/ml-engine/<x>/<y>/<year>/<part>/prediction.results-00000-of-00001
  bucket, _, x, y, year, part, _ = ml_engine_file.lstrip('gs://').split('/')
  landcover_file_prefix = 'landcover/{}/{}/{}/{}.tfrecord'.format(x, y, year, part)
  landcover_file = 'gs://{}/{}'.format(bucket, landcover_file_prefix)
  logging.info('landcover_file: ' + landcover_file)

  with tf.io.TFRecordWriter(landcover_file) as output_file:
    with tf.gfile.Open(ml_engine_file) as input_file:
      for line in input_file:
        # Make a patch tf.train.Example from prediction data.
        data = json.loads(line)
        patch = tf.convert_to_tensor(data['predictions'])
        print('patch')
        example = tf.train.Example(
          features=tf.train.Features(
            feature={
              'landcover': tf.train.Feature(
                # int64_list=tf.train.Int64List(value=tf.reshape(patch, [-1]))
                bytes_list=tf.train.BytesList(value=tf.reshape(patch, [-1]))
              )
            }
          )
        )
        output_file.write(example.SerializeToString())
  logging.info('done: ' + landcover_file)


if __name__ == '__main__':
  import argparse

  parser = argparse.ArgumentParser()
  parser.add_argument(
      '--ml-engine-file',
      type=str,
      default=None,
  )
  args = parser.parse_args()

  logging.basicConfig(level=logging.INFO)
  run(args.ml_engine_file)
