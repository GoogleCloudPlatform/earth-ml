import ee
import mercantile
import os

import landsat_image

BUCKET = os.environ['BUCKET']
REGION_ZOOM_LEVEL = int(os.environ['REGION_ZOOM_LEVEL'])


def region(x, y, start_year, end_year):
  return [
      request_ee_task(x, y, year)
      for year in range(start_year, end_year+1)
  ]


def point(lng, lat, start_year, end_year):
  tile = mercantile.tile(lng, lat, REGION_ZOOM_LEVEL)
  return region(tile.x, tile.y, start_year, end_year)


def bounds(west, south, east, north, start_year, end_year):
  return [
      region(tile.x, tile.y, start_year, end_year)
      for tile in mercantile.tiles(west, south, east, north, REGION_ZOOM_LEVEL)
  ]


def tile(x, y, zoom, start_year, end_year):
  xy_bounds = mercantile.xy_bounds(x, y, zoom)
  west, north = mercantile.lnglat(xy_bounds.left, xy_bounds.top)
  east, south = mercantile.lnglat(xy_bounds.right, xy_bounds.bottom)
  return bounds(west, south, east, north, start_year, end_year)


def request_ee_task(x, y, year):
  # Get the region bounds to build a polygon.
  bounds = mercantile.bounds(x, y, REGION_ZOOM_LEVEL)
  north = bounds.north
  east = bounds.east + 0.1
  south = bounds.south - 0.1
  west = bounds.west

  # Start the task asynchronously to export to Google Cloud Storage.
  path_prefix = f"regions/{x}/{y}/{year}/"
  task = ee.batch.Export.image.toCloudStorage(
      image=landsat_image.get(year),
      description=f"{x}-{y}-{year}",
      bucket=BUCKET,
      fileNamePrefix=path_prefix,
      region=[
          [east, north],
          [west, north],
          [west, south],
          [east, south],
          [east, north],
      ],
      scale=30,
      maxPixels=int(1e10),
      crs='EPSG:4326',
      fileFormat='TFRecord',
      formatOptions={
          'patchDimensions': [256, 256],
          'kernelSize': [32, 32],
          'compressed': True,
      },
      maxWorkers=2000,
  )
  # task.start()
  print(f"{x}-{y}-{year}: started task {task.id} [{west},{south},{east},{north})")

  return {
      'ee_task_id': task.id,
      'bucket': BUCKET,
      'path_prefix': path_prefix,
      'north': north,
      'east': east,
      'south': south,
      'west': west,
  }
