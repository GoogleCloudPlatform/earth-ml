import json
import logging
import os
from google.cloud import pubsub

import tensorflow as tf
tf.enable_eager_execution()

PROJECT = os.environ['PROJECT']
ML_ENGINE_TOPIC = os.environ['ML_ENGINE_TOPIC']

subscriber = pubsub.SubscriberClient()


def run():
  print("Listening...")
  future = subscriber.subscribe(
      subscription=subscriber.subscription_path(PROJECT, ML_ENGINE_TOPIC),
      callback=ml_engine_callback,
  )
  future.result()


def ml_engine_callback(message):
  message.ack()

  ml_engine_file = message.data.decode('utf-8')
  logging.info('ml_engine_file: ' + ml_engine_file)

  # gs://<bucket>/ml-engine/<x>/<y>/<year>/<part>/prediction.results-00000-of-00001
  bucket, _, x, y, year, part, _ = ml_engine_file.lstrip('gs://').split('/')
  landcover_file = 'gs://{}/landcover/{}/{}/{}/{}.tfrecord'.format(bucket, x, y, year, part)
  logging.info('landcover_file: ' + landcover_file)

  with tf.io.TFRecordWriter(landcover_file) as output_file:
    with tf.gfile.Open(ml_engine_file) as input_file:
      for line in input_file:
        # Make a patch tf.train.Example from prediction data.
        data = json.loads(line)
        patch = tf.convert_to_tensor(data['predictions'])
        example = tf.train.Example(
          features=tf.train.Features(
            feature={
              'landcover': tf.train.Feature(
                int64_list=tf.train.Int64List(value=tf.reshape(patch, [-1]))
              )
            }
          )
        )
        output_file.write(example.SerializeToString())
  logging.info('done: ' + landcover_file)


if __name__ == '__main__':
  logging.basicConfig(level=logging.INFO)
  run()
