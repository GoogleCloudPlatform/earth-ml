import ee
import json
import os
import subprocess as sp

import config


def run(x, y, year, parts):
  region_id = f"{x}-{y}-{year}"
  print(f"region_id: {region_id}")

  landcover_files = [
      f"gs://{config.BUCKET}/landcover/{x}/{y}/{year}/{part:05}.tfrecord"
      for part in range(parts)
  ]
  print(f"landcover_files: {landcover_files[0]}, ... ({len(landcover_files)} files)")

  mixer_file = f"gs://{config.BUCKET}/regions/{x}/{y}/{year}/mixer.json"
  print(f"mixer_file: {mixer_file}")

  asset_id = f"{config.ASSET_ID}/{region_id}"
  print(f"asset_id: {asset_id}")

  # If the asset already exists, skip it.
  if ee.data.getInfo(asset_id) is not None:
    print(f"Skipping upload, asset already exists: {asset_id}")
    return asset_id

  command = config.earthengine + ['upload', 'image']
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
