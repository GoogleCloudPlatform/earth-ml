import ee
import os
import subprocess as sp
from collections import OrderedDict

import config


def check_progress(x, y):
  result = OrderedDict()
  result['x'] = x
  result['y'] = y
  result['config'] = {
      'PROJECT': config.PROJECT,
      'BUCKET': config.BUCKET,
      'ASSET_ID': config.ASSET_ID,
      'region_zoom_level': config.region_zoom_level,
  }

  # Look for the most recent EE task.
  tasks = ee.batch.Task.list()

  # Analyze the contents for the regions directory.
  info = result['regions'] = OrderedDict()
  prefix = f"regions/{x}/{y}/"
  info['path'] = f"gs://{config.BUCKET}/{prefix}"
  for blob in config.bucket.list_blobs(prefix=prefix):
    abs_path = f"gs://{config.BUCKET}/{blob.name}"
    valid = True
    try:
      year, filename = blob.name[len(prefix):].split('/', 1)
      year = int(year)
      if year not in info:
        info[year] = OrderedDict()
        info[year]['tfrecord_files'] = 0
        info[year]['mixer_file'] = False
      if filename.endswith('.tfrecord.gz'):
        info[year]['tfrecord_files'] += 1
      elif filename == 'mixer.json':
        info[year]['mixer_file'] = True
      else:
        valid = False
    except:
      valid = False
    if not valid:
      if 'unknown_files' not in info:
        info['unknown_files'] = []
      info['unknown_files'] += [abs_path]

  # Analyze the contents for the ml-engine directory.
  info = result['ml-engine'] = OrderedDict()
  prefix = f"ml-engine/{x}/{y}/"
  info['path'] = f"gs://{config.BUCKET}/{prefix}"
  for blob in config.bucket.list_blobs(prefix=prefix):
    abs_path = f"gs://{config.BUCKET}/{blob.name}"
    valid = True
    try:
      year, _, filename = blob.name[len(prefix):].split('/', 2)
      year = int(year)
      if year not in info:
        info[year] = 0
      if filename.startswith('prediction.results'):
        info[year] += 1
      elif filename.startswith('prediction.errors'):
        if blob.size != 0:
          if 'errors' not in info:
            info['errors'] = []
          info['errors'] += [{
            'file': abs_path,
            'error': blob.download_as_string().decode('utf-8'),
          }]
      else:
        valid = False
    except:
      valid = False
    if not valid:
      if 'unknown_files' not in info:
        info['unknown_files'] = []
      info['unknown_files'] += [abs_path]

  # Analyze the contents for the landcover directory.
  info = result['landcover'] = OrderedDict()
  prefix = f"landcover/{x}/{y}/"
  info['path'] = f"gs://{config.BUCKET}/{prefix}"
  for blob in config.bucket.list_blobs(prefix=prefix):
    abs_path = f"gs://{config.BUCKET}/{blob.name}"
    valid = True
    try:
      year, filename = blob.name[len(prefix):].split('/', 1)
      year = int(year)
      if year not in info:
        info[year] = 0
      if filename.endswith('.tfrecord'):
        info[year] += 1
      else:
        valid = False
    except:
      valid = False
    if not valid:
      if 'unknown_files' not in info:
        info['unknown_files'] = []
      info['unknown_files'] += [abs_path]

  # Check the Earth Engine asset upload task.
  info = result['upload'] = OrderedDict()
  for task in tasks:
    if task.task_type == 'INGEST':
      # Example description:
      #   "Asset ingestion: projects/project/landcover/46-97-2018"
      region_id = task.config['description'].rsplit('/', 1)[-1]
      task_x, task_y, year = [int(part) for part in region_id.split('-')]
      if task_x != x or task_y != y:
        continue
      if year not in info:
        info[year] = OrderedDict()
      info[year]['task_id'] = task.id

  return result


def list_ee_tasks():
  return [
      str(task).lstrip('<').rstrip('>')
      for task in ee.batch.Task.list()
  ]


def clear_image_collections():
  outputs = ''
  command = config.earthengine + ['rm', '-v', '-r', config.ASSET_ID]
  result = sp.run(command, capture_output=True)
  outputs += f">> {command}\n"
  outputs += f"{result.stdout.decode('utf-8')}"
  outputs += f"stderr: {result.stderr.decode('utf-8')}"
  outputs += "\n\n"

  command = config.earthengine + ['create', 'collection', config.ASSET_ID]
  result = sp.run(command, capture_output=True)
  outputs += f">> {command}\n"
  outputs += f"{result.stdout.decode('utf-8')}"
  outputs += f"stderr: {result.stderr.decode('utf-8')}"
  outputs += "\n\n"

  return outputs
