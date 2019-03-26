import ee
import json
import logging
import mercantile
import time
from google.cloud import pubsub

from classifier import cache
from classifier import config


def tile(tile_x, tile_y, zoom, year):
  # Wait for all regions to finish processing.
  for region in request_tile_regions(tile_x, tile_y, zoom, year):
    while region['id'] not in cache.regions:
      time.sleep(5)
    while not cache.regions[region['id']]['done']:
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


def request_tile_regions(tile_x, tile_y, zoom, year):
  publisher = pubsub.PublisherClient()
  topic_path = publisher.topic_path(config.project, config.regions_topic)

  regions = tile_to_regions(tile_x, tile_y, zoom, year)
  for region in regions:
    if region['id'] in cache.regions:
      cached = cache.regions[region['id']]

      # If the region is done, skip it.
      if cached['done']:
        continue

    # Otherwise, request the region for processing.
    logging.info('requesting region {}'.format(region['id']))
    cache.regions[region['id']] = {
        'done': False,
    }
    publisher.publish(
        topic=topic_path,
        data=json.dumps(region, separators=(',', ':')).encode('utf-8'),
        id=region['id'],
    )
  return regions


def tile_to_regions(tile_x, tile_y, zoom, year):
  tile = mercantile.xy_bounds(tile_x, tile_y, zoom)
  west, north = mercantile.lnglat(tile.left, tile.top)
  east, south = mercantile.lnglat(tile.right, tile.bottom)

  regions = []
  for region in mercantile.tiles(west, south, east, north, config.region_zoom):
    bounds = mercantile.bounds(region)
    region = {
      'id': '{}-{}-{}'.format(region.x, region.y, year),
      'x': region.x,
      'y': region.y,
      'year': year,
      'north': bounds.north,
      'east': bounds.east + 0.1,
      'south': bounds.south - 0.1,
      'west': bounds.west,
    }
    regions += [region]
  return regions
