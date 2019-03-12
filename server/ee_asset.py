import datetime
import ee
import json
import logging
import os
import subprocess as sp
import time

from google.cloud import pubsub
from supermercado.uniontiles import mercantile

import config
from cache import Cache

blocks_cache = Cache('blocks')


def tile_url(x, y, zoom, year):
  publisher = pubsub.PublisherClient()
  topic_path = publisher.topic_path(config.project, config.pipeline_topic)  # pylint: disable=no-member

  blocks = tileToBlocks(x, y, zoom, year)
  for block in blocks:
    if block['id'] in blocks_cache:
      cached = blocks_cache[block['id']]

      # If the block is done, skip it.
      if cached['done']:
        continue

      # If the block was started within the last hour, skip it.
      now_minus_1hr = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(hours=1)
      if now_minus_1hr < cached['date']:
        continue

    # Otherwise, request the block for processing.
    logging.info('Requesting block {}'.format(block['id']))
    blocks_cache[block['id']] = {
        'done': False,
        'date': datetime.datetime.now(datetime.timezone.utc),
    }
    publisher.publish(
        topic=topic_path,
        data=json.dumps(block, separators=(',', ':')).encode('utf-8'),
        id=block['id'],
    )

  # Wait for all blocks to finish processing.
  for block in blocks:
    while block['id'] not in blocks_cache:
      time.sleep(5)
    while not blocks_cache[block['id']]['done']:
      time.sleep(5)

  # Return the tile URL from the uploaded asset image collection.
  asset_id = '/'.join([config.ee_project, config.ee_image_collection])
  mapid = ee.ImageCollection(asset_id).getMapId({
    'min': 0,
    'max': len(config.classifications),
    'palette': config.palette,
  })
  return ee.data.getTileUrl(mapid, x, y, zoom)


def tileToBlocks(tile_x, tile_y, zoom, year):
  tile = mercantile.xy_bounds(tile_x, tile_y, zoom)
  west, north = mercantile.lnglat(tile.left, tile.top)
  east, south = mercantile.lnglat(tile.right, tile.bottom)

  blocks = []
  for block in mercantile.tiles(west, south, east, north, config.block_zoom):
    bounds = mercantile.bounds(block)
    block = {
      'id': '{}-{}-{}'.format(block.x, block.y, year),
      'x': block.x,
      'y': block.y,
      'year': year,
      'north': bounds.north,
      'east': bounds.east,
      'south': bounds.south,
      'west': bounds.west,
    }
    blocks += [block]
  return blocks


def upload(block_id, predictions_file, mixer_file):
  asset_id = '/'.join([config.ee_project, config.ee_image_collection, block_id])
  command = [
      'earthengine',
      '--service_account_file', os.environ['GOOGLE_APPLICATION_CREDENTIALS'],
      'upload', 'image', predictions_file, mixer_file,
      '--asset_id', asset_id,
      '--wait',
  ]
  result = sp.run(command, capture_output=True)
  if result.returncode == 0:
    blocks_cache.update_fields(block_id, {'done': True})
  return {
      'asset_id': asset_id,
      'returncode': result.returncode,
      'stdout': result.stdout.decode('utf-8'),
      'stderr': result.stderr.decode('utf-8'),
  }
