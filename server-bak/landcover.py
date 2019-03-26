import datetime
import ee
import json
import logging
import mercantile
import time
from google.cloud import pubsub

import cache
import config


def request_tile_blocks(tile_x, tile_y, zoom, year):
  publisher = pubsub.PublisherClient()
  topic_path = publisher.topic_path(config.project, config.pipeline_topic)  # pylint: disable=no-member

  blocks = tile_to_blocks(tile_x, tile_y, zoom, year)
  for block in blocks:
    if block['id'] in cache.blocks:
      cached = cache.blocks[block['id']]

      # If the block is done, skip it.
      if cached['done']:
        continue

      # If the block was started (and not done) within the last hour, skip it.
      now_minus_1hr = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(hours=1)
      if now_minus_1hr < cached['date']:
        continue

    # Otherwise, request the block for processing.
    logging.info('requesting block {}'.format(block['id']))
    cache.blocks[block['id']] = {
        'date': datetime.datetime.now(datetime.timezone.utc),
        'done': False,
    }
    publisher.publish(
        topic=topic_path,
        data=json.dumps(block, separators=(',', ':')).encode('utf-8'),
        id=block['id'],
    )
  return blocks


def tile_url(tile_x, tile_y, zoom, year):
  # Wait for all blocks to finish processing.
  for block in request_tile_blocks(tile_x, tile_y, zoom, year):
    while block['id'] not in cache.blocks:
      time.sleep(5)
    while not cache.blocks[block['id']]['done']:
      time.sleep(5)

  # Return the tile URL from the uploaded asset image collection.
  asset_id = '/'.join([config.ee_project, config.ee_image_collection])
  mapid = (
      ee.ImageCollection(asset_id)
      .filterDate('{}-1-1'.format(year-1), '{}-1-1'.format(year))
      .getMapId({
          'min': 0,
          'max': len(config.classifications),
          'palette': config.palette,
      })
  )
  return ee.data.getTileUrl(mapid, tile_x, tile_y, zoom)


def tile_to_blocks(tile_x, tile_y, zoom, year):
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
      'east': bounds.east + 0.1,
      'south': bounds.south - 0.1,
      'west': bounds.west,
    }
    blocks += [block]
  return blocks
