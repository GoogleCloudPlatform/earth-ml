import logging
import os
import subprocess as sp

from classifier import cache
from classifier import config

earthengine = [
    'earthengine',
    '--service_account_file', os.environ['GOOGLE_APPLICATION_CREDENTIALS'],
]


def upload(region_id, classifications_file, mixer_file):
  _, _, year = region_id.split('-')
  asset_id = '/'.join([config.ee_project, config.ee_image_collection, region_id])
  if region_id in cache.regions and cache.regions[region_id].get('done') == True:
    return {'asset_id': asset_id}

  command = earthengine + [
      'upload', 'image', classifications_file, mixer_file,
      '--asset_id', asset_id,
      '--time_start', '{}-1-1'.format(int(year)-1),
      '--time_end', '{}-1-1'.format(year),
      '--force', '--wait',
  ]
  logging.info('{}: running {}'.format(region_id, command))
  result = sp.run(command, capture_output=True)
  if result.returncode == 0:
    cache.regions.update_fields(region_id, {'done': True})
  logging.info('{}: returncode={}'.format(region_id, result.returncode))
  logging.info('{}: stdout: {}'.format(region_id, result.stdout.decode('utf-8')))
  logging.info('{}: stderr: {}'.format(region_id, result.stderr.decode('utf-8')))
  return {
      'asset_id': asset_id,
      'returncode': result.returncode,
      'stdout': result.stdout.decode('utf-8'),
      'stderr': result.stderr.decode('utf-8'),
  }
