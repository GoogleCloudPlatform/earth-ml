import json
import os
import requests
from datetime import datetime
# from google.cloud import pubsub
from google.cloud import storage

PROJECT = os.environ['PROJECT']
# ML_ENGINE_TOPIC = os.environ['ML_ENGINE_TOPIC']

server_url = f"https://server-dot-{PROJECT}.appspot.com"
classifier_url = "http://35.222.125.215:7070"

# Configure the Google Cloud client libraries.
storage_client = storage.Client()
# publisher = pubsub.PublisherClient()
# ml_engine_topic = publisher.topic_path(PROJECT, ML_ENGINE_TOPIC)


def dispatch(event, context):
  """Triggered by a change to a Cloud Storage bucket.
  Args:
    event (dict): Event payload.
    context (google.cloud.functions.Context): Metadata for the event.
  """
  bucket = event['bucket']
  file_path = event['name']

  # Ignore beam temporary files.
  if 'beam-temp' in file_path:
    return

  run(bucket, file_path)


def run(bucket, file_path):
  print(f"===--- {file_path} ---===")

  abs_path = f"gs://{bucket}/{file_path}"
  dirname, x, y, year, filename = file_path.split('/', 4)
  if dirname == 'regions':
    handle_regions_file(abs_path, bucket, x, y, year, filename)
  # elif dirname == 'ml-engine':
  #   handle_ml_engine_file(abs_path, bucket, x, y, year, filename)
  elif dirname == 'landcover':
    handle_landcover_file(abs_path, bucket, x, y, year, filename)
  else:
    print(f"No matching handler, ignoring: {abs_path}")


def handle_regions_file(abs_path, bucket, x, y, year, filename):
  if filename.endswith('.tfrecord.gz'):
    # As data is extracted, .tfrecord.gz files start appearing.
    part = filename.split('.', 1)[0]
    timestamp = datetime.now().strftime('%Y%m%d-%H%M%S')
    job_id = f"landcover-{x}-{y}-{year}-{part}-{timestamp}"
    input_path = f"gs://{bucket}/regions/{x}/{y}/{year}/{filename}"
    output_path_prefix = f"landcover/{x}/{y}/{year}/{part}.tfrecord"
    output_path = f"gs://{bucket}/{output_path_prefix}"
    gcs_bucket = storage_client.bucket(bucket)
    if gcs_bucket.blob(output_path_prefix).exists():
      print(f"Skipping classification, landcover file exists: {output_path}")
      return
    requests.post(f"{classifier_url}/process", json={
        'name': job_id,
        'input': input_path,
        'output': output_path,
    })
    print(f"Classification job requested: {abs_path}")
    print(f"  job_id: {job_id}")
    print(f"  input_path: {input_path}")
    print(f"  output_path: {output_path}")
  else:
    print(f"No action for file, ignoring: {abs_path}")


# def handle_ml_engine_file(abs_path, bucket, x, y, year, filename):
#   if 'prediction.results' in filename:
#     import tensorflow as tf
#     tf.enable_eager_execution()

#     # We are using a pre-computed Example header to make it faster
#     # since all the patches are the same shape.
#     example_header = b'\n\x9b\x80\x04\n\x97\x80\x04\n\tlandcover\x12\x88\x80\x04\x1a\x84\x80\x04\n\x80\x80\x04'

#     # These are the output files from ML Engine batch prediction.
#     # We publish them to ml_engine_topic to have the workers convert it to TFRecord.
#     part, _ = filename.split('/', 1)
#     ml_engine_file = abs_path
#     landcover_file = f"gs://{bucket}/landcover/{x}/{y}/{year}/{part}.tfrecord"
#     with tf.io.TFRecordWriter(landcover_file) as output_file:
#       with tf.gfile.Open(ml_engine_file) as input_file:
#         for line in input_file:
#           # Make a serialized tf.train.Example for all the patches.
#           data = json.loads(line)
#           patch = tf.convert_to_tensor(data['predictions'], tf.int8)
#           array_as_bytes = tf.reshape(patch, [-1]).numpy().tobytes()
#           serialized_example = example_header + array_as_bytes
#           output_file.write(serialized_example)
#   else:
#     print(f"No action for file, ignoring: {abs_path}")


def handle_landcover_file(abs_path, bucket, x, y, year, filename):
  if filename.endswith('.tfrecord'):
    # These are the now converted results from ML Engine as TFRecords.
    # Check that all the files have finished.
    gcs_bucket = storage_client.bucket(bucket)

    regions_prefix = f"regions/{x}/{y}/{year}"
    total_parts = 0
    mixer_file_found = False
    for blob in gcs_bucket.list_blobs(prefix=regions_prefix):
      if blob.name.endswith('.tfrecord.gz'):
        total_parts += 1
      elif blob.name.endswith('mixer.json'):
        mixer_file_found = True

    if not mixer_file_found:
      print(f"Mixer file not found, extraction is not done: {abs_path}")
      return

    parts_found = 0
    for part in range(total_parts):
      landcover_prefix = f"landcover/{x}/{y}/{year}/{part:05}.tfrecord"
      if gcs_bucket.blob(landcover_prefix).exists():
        parts_found += 1
    print(f"{parts_found} of {total_parts} parts finished: {abs_path}")
    if parts_found == total_parts:
      print(f"All parts finished, requesting upload to Earth Engine: {abs_path}")
      request('region/upload', x=x, y=y, year=year, parts=total_parts)
  else:
    print(f"No action for file, ignoring: {abs_path}")


def request(action, **kwargs):
  # Does an asynchronous POST request, we don't need to wait for results.
  url = f"{server_url}/{action}"
  print(f"POST {url} params={kwargs}")
  requests.post(url, params=kwargs)


if __name__ == '__main__':
  import argparse

  parser = argparse.ArgumentParser()
  parser.add_argument('gcs_path', help='Google Cloud Storage path')
  args = parser.parse_args()

  bucket, path_prefix = args.gcs_path.lstrip('gs://').split('/', 1)
  gcs_bucket = storage_client.bucket(bucket)
  for blob in gcs_bucket.list_blobs(prefix=path_prefix):
    print(blob.name)
    run(bucket, blob.name)
