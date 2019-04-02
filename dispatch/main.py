import os
import requests
from google.cloud import pubsub
from google.cloud import storage

PROJECT = os.environ['PROJECT']
SERVER = os.environ['SERVER']
ML_ENGINE_TOPIC = os.environ['ML_ENGINE_TOPIC']

# Configure the Google Cloud client libraries.
storage_client = storage.Client()
publisher = pubsub.PublisherClient()
ml_engine_topic = publisher.topic_path(PROJECT, ML_ENGINE_TOPIC)


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
  print(f"dirname={dirname}, x={x}, y={y}, year={year}, filename={filename}")
  if dirname == 'regions':
    handle_regions_file(abs_path, bucket, x, y, year, filename)
  elif dirname == 'ml-engine':
    handle_ml_engine_file(abs_path, bucket, x, y, year, filename)
  elif dirname == 'landcover':
    handle_landcover_file(abs_path, bucket, x, y, year, filename)
  else:
    print(f"No matching handler, ignoring: gs://{bucket}/{file_path}")


def handle_regions_file(abs_path, bucket, x, y, year, filename):
  if filename.endswith('.tfrecord.gz'):
    # As data is extracted, .tfrecord.gz files start appearing.
    # The last file to appear is the mixer.json file, but we can ignore it for now.
    part = int(filename.rstrip('.tfrecord.gz'))
    request('region/classify', x=x, y=y, year=year, part=part)
  else:
    print(f"No action for file, ignoring: {abs_path}")


def handle_ml_engine_file(abs_path, bucket, x, y, year, filename):
  if 'prediction.results' in filename:
    # These are the output files from ML Engine batch prediction.
    # We publish them to ml_engine_topic to have the workers convert it to TFRecord.
    print(f"Published {abs_path} to {ml_engine_topic}")
    publisher.publish(ml_engine_topic, abs_path.encode('utf-8'))
  else:
    print(f"No action for file, ignoring: {abs_path}")


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
      print(f"Mixer file not found, extraction is not done")
      return

    print(f"Found {total_parts} region parts")
    for part in range(total_parts):
      landcover_prefix = f"landcover/{x}/{y}/{year}/{part:05}.tfrecord"
      if not gcs_bucket.blob(landcover_prefix).exists():
        print(f"Not all parts are done: gs://{bucket}/{landcover_prefix}")
        return
    print(f"All parts finished, requesting upload to Earth Engine")
    request('region/upload', x=x, y=y, year=year, total_parts=total_parts)
  else:
    print(f"No action for file, ignoring: {abs_path}")


def request(action, **kwargs):
  # Does an asynchronous POST request, we don't need to wait for results.
  url = f"{SERVER}/{action}"
  print(f"POST {url} params={kwargs}")
  requests.post(url, params=kwargs)


if __name__ == '__main__':
  import argparse

  parser = argparse.ArgumentParser()
  parser.add_argument(
      'gcs_path', help='Google Cloud Storage path, including gs://')
  args = parser.parse_args()

  bucket, filename = args.gcs_path.lstrip('gs://').split('/', 1)
  run(bucket, filename)
