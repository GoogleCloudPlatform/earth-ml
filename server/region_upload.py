import json
import os
import subprocess as sp

BUCKET = os.environ['BUCKET']
EE_PROJECT = os.environ['EE_PROJECT']
EE_IMAGE_COLLECTION = os.environ.get('EE_IMAGE_COLLECTION', 'landcover')

earthengine = [
    'earthengine',
    '--service_account_file', os.environ['GOOGLE_APPLICATION_CREDENTIALS'],
]


def run(x, y, year, parts):
  region_id = f"{x}-{y}-{year}"
  print(f"region_id: {region_id}")

  landcover_files = [
      f"gs://{BUCKET}/landcover/{x}/{y}/{year}/{part:05}.tfrecord"
      for part in range(parts)
  ]
  print(f"landcover_files: {landcover_files[0]}, ... ({len(landcover_files)} files)")

  mixer_file = f"gs://{BUCKET}/regions/{x}/{y}/{year}/mixer.json"
  print(f"mixer_file: {mixer_file}")

  asset_id = '/'.join([EE_PROJECT, EE_IMAGE_COLLECTION, region_id])
  print(f"asset_id: {asset_id}")

  command = earthengine + ['upload', 'image']
  command += landcover_files
  command += [
      mixer_file,
      '--asset_id', asset_id,
      '--time_start', f"{year}-1-1",
      '--time_end', f"{year}-12-31",
      '--force',
  ]
  print(f"command: {command}")
  result = sp.run(command, capture_output=True)
  print(f"returncode={result.returncode}")
  print(f"stdout: {result.stdout.decode('utf-8')}")
  print(f"stderr: {result.stderr.decode('utf-8')}")

  if result.returncode != 0:
    return {
        'asset_id': asset_id,
        'returncode': result.returncode,
        'stdout': result.stdout.decode('utf-8'),
        'stderr': result.stderr.decode('utf-8'),
    }

  return asset_id
