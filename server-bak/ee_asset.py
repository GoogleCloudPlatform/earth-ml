import logging
import os
import subprocess as sp

import cache
import config

earthengine = [
    'earthengine',
    '--service_account_file', os.environ['GOOGLE_APPLICATION_CREDENTIALS'],
]


def upload(block_id, predictions_file, mixer_file):
  _, _, year = block_id.split('-')
  asset_id = '/'.join([config.ee_project, config.ee_image_collection, block_id])
  if block_id in cache.blocks and cache.blocks[block_id].get('done') == True:
    return {'asset_id': asset_id}

  command = earthengine + [
      'upload', 'image', predictions_file, mixer_file,
      '--asset_id', asset_id,
      '--time_start', '{}-1-1'.format(int(year)-1),
      '--time_end', '{}-1-1'.format(year),
      '--force', '--wait',
  ]
  logging.info('{}: running {}'.format(block_id, command))
  result = sp.run(command, capture_output=True)
  if result.returncode == 0:
    cache.blocks.update_fields(block_id, {'done': True})
  logging.info('{}: returncode={}'.format(block_id, result.returncode))
  logging.info('{}: stdout: {}'.format(block_id, result.stdout.decode('utf-8')))
  logging.info('{}: stderr: {}'.format(block_id, result.stderr.decode('utf-8')))
  return {
      'asset_id': asset_id,
      'returncode': result.returncode,
      'stdout': result.stdout.decode('utf-8'),
      'stderr': result.stderr.decode('utf-8'),
  }
