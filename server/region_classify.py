import os
import time
from googleapiclient import discovery
from googleapiclient import errors

import config

model = 'landcover'
version = None
batch_size = 16
gce_region = 'us-central1'
# max_workers = 50


def run(x, y, year, part):
  input_path = f"gs://{config.BUCKET}/regions/{x}/{y}/{year}/{part:05}.tfrecord.gz"
  print(f"input_path: {input_path}")

  output_path = f"gs://{config.BUCKET}/ml-engine/{x}/{y}/{year}/{part:05}/"
  print(f"output_path: {output_path}")

  # Create a unique job name using the current timestamp.
  timestamp = time.strftime('%Y%m%d_%H%M%S', time.gmtime())
  job_id = f"{model}_{x}_{y}_{year}_{part}__{timestamp}"

  # Start building the request dictionary with required information.
  job_body = {
      'jobId': job_id,
      'predictionInput': {
          'inputPaths': input_path,
          'outputPath': output_path,
          'dataFormat': 'tf-record-gzip',
          'batchSize': batch_size,
          'region': gce_region,
          # 'maxWorkerCount': max_workers,
      }
  }

  # Use the version if present, the model (its default version) if not.
  project_path = f"projects/{config.PROJECT}"
  print(f"project_path: {project_path}")

  model_path = f"{project_path}/models/{model}"
  print(f"model_path: {model_path}")

  if version:
    version_path = f"{model_path}/versions/{version}"
    job_body['predictionInput']['versionName'] = version_path
    print(f"version_path: {version_path}")
  else:
    job_body['predictionInput']['modelName'] = model_path

  # Create the ML Engine job request.
  ml = discovery.build('ml', 'v1')
  request = ml.projects().jobs().create(
      parent=project_path,
      body=job_body,
  )

  retry = True
  while retry:
    try:
      request.execute()
      print(f"Job requested, job_id: {job_id}")
      retry = False

    except errors.HttpError as error:
      # Something went wrong, print out some information.
      error_message = error._get_reason()
      print(error_message)
      quota_error = (
          'The allowed Cloud ML quota for API calls in the '
          '"Job submission requests" group is exceeded'
      )
      if quota_error in error_message:
        # There is a quota for 60 requests every 60 seconds,
        # so try again in 61 seconds.
        time.sleep(61)
        retry = True

  return job_id