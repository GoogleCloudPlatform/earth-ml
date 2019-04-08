import ee
import mercantile
import os

import config
import landsat_image


def region(x, y, start_year, end_year, dry_run=False):
  return [
      request_ee_task(x, y, year, dry_run)
      for year in range(start_year, end_year+1)
  ]


def point(lng, lat, start_year, end_year, dry_run=False):
  tile = mercantile.tile(lng, lat, config.region_zoom_level)
  return region(tile.x, tile.y, start_year, end_year, dry_run)


def bounds(west, south, east, north, start_year, end_year, dry_run=False):
  return [
      region(tile.x, tile.y, start_year, end_year, dry_run)
      for tile in mercantile.tiles(west, south, east, north, config.region_zoom_level)
  ]


def tile(x, y, zoom, start_year, end_year, dry_run=False):
  xy_bounds = mercantile.xy_bounds(x, y, zoom)
  west, north = mercantile.lnglat(xy_bounds.left, xy_bounds.top)
  east, south = mercantile.lnglat(xy_bounds.right, xy_bounds.bottom)
  return bounds(west, south, east, north, start_year, end_year, dry_run)


def request_ee_task(x, y, year, dry_run=False):
  # Get the region bounds to build a polygon.
  bounds = mercantile.bounds(x, y, config.region_zoom_level)
  north = bounds.north
  east = bounds.east + 0.1
  south = bounds.south - 0.1
  west = bounds.west

  # Start the task asynchronously to export to Google Cloud Storage.
  region_id = f"{x}-{y}-{year}"
  output_path_prefix = f"regions/{x}/{y}/{year}/"
  output_path = f"gs://{config.BUCKET}/{output_path_prefix}"
  task = ee.batch.Export.image.toCloudStorage(
      image=landsat_image.get(year),
      description=region_id,
      bucket=config.BUCKET,
      fileNamePrefix=output_path_prefix,
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

  if dry_run:
    print(f"This is a dry run, task {task.id} will NOT be submitted.")
  elif config.bucket.blob(output_path_prefix + '00000.tfrecord.gz').exists():
    # A file already exists, that means an extraction is already in process.
    print(f"Skipping extraction, found: {output_path_prefix + '00000.tfrecord.gz'}")
  else:
    task_found = False
    for t in ee.batch.Task.list():
      if t.state in ('READY', 'RUNNING') and \
          t.task_type == 'EXTRACT_IMAGE' and \
          t.config['description'] == region_id:
        print(f"Skipping extraction, found task: {t.id}")
        task_found = True
        break
    if not task_found:
      task.start()
      print(f"{x}-{y}-{year}: started task {task.id} [{west},{south},{east},{north})")

  return {
      'task_id': task.id,
      'output_path': output_path,
      'north': north,
      'east': east,
      'south': south,
      'west': west,
  }
