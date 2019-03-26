import ee
import logging
import time

from classifier import cache
from classifier import config

active_states = (
    ee.batch.Task.State.READY,
    ee.batch.Task.State.RUNNING,
)


def tile(x, y, zoom, year):
  mapid = get_image(year).getMapId(config.ee_vis_params)
  return ee.data.getTileUrl(mapid, x, y, zoom)


def region(region_id, x, y, year, north, east, south, west):
  prefix = '{}/{}/{}'.format(x, y, year)
  file_prefix = 'gs://{}/{}'.format(config.regions_bucket, prefix)
  inputs_file = file_prefix + '.tfrecord.gz'
  mixer_file = file_prefix + '.json'
  classifications_file = 'gs://{}/{}'.format(config.classifications_bucket, prefix)
  result = {
    'id': region_id,
    'inputs_file': inputs_file,
    'mixer_file': mixer_file,
    'classifications_file': classifications_file,
  }

  if cache.gcs_file_exists(inputs_file) and cache.gcs_file_exists(inputs_file):
    logging.info('{}: found {}'.format(region_id, inputs_file))
    return result

  task_id = None
  if region_id in cache.regions:
    cached_region = cache.regions[region_id]
    if 'task_id' in cached_region:
      task_id = cached_region['task_id']
      if ee.data.getTaskStatus(task_id)[0] not in active_states:
        task_id = None

  if task_id is None:
    # Start the task asynchronously to export to Google Cloud Storage.
    task = ee.batch.Export.image.toCloudStorage(
        image=get_image(year),
        description=region_id,
        bucket=config.regions_bucket,
        fileNamePrefix=prefix,
        region=[
            [east, north],
            [west, north],
            [west, south],
            [east, south],
            [east, north],
        ],
        crs='EPSG:4326',
        scale=30,
        fileFormat='TFRecord',
        formatOptions={
            'patchDimensions': [config.tile_size, config.tile_size],
            'kernelSize': [config.cnn_patch_size, config.cnn_patch_size],
            'compressed': True,
        },
        maxWorkers=2000,
    )
    task.start()

    task_id = task.id
    cache.regions.update_fields(region_id, {
      'task_id': task_id,
    })
    logging.info('{}: started task {}'.format(region_id, task_id))

  wait_for_task(task_id)
  return result


def get_image(year):
  def mask_clouds(landsat8):
    qa = landsat8.select('pixel_qa')
    return landsat8.updateMask(
        qa.bitwiseAnd(1 << 3).eq(0)        # Cloud shadow bit
        .And(qa.bitwiseAnd(1 << 5).eq(0))  # Cloud bit
    )

  start_year = ee.Number(year).subtract(1)
  start_date = ee.Date.fromYMD(start_year, 1, 1)
  end_date = ee.Date.fromYMD(year, 1, 1)

  landsat8 = (
      ee.ImageCollection('LANDSAT/LC08/C01/T1_SR')
      .filterDate(start_date, end_date)
      .map(mask_clouds)
      .median()
  )

  raw_elevation = ee.Image('USGS/GMTED2010').rename('elevation')
  elevation_range = raw_elevation.reduceRegion(
      reducer=ee.Reducer.minMax(),
      scale=8000,
  )
  elevation = (
      raw_elevation
      .subtract(ee.Image.constant(elevation_range.get('elevation_min')))
      .divide(ee.Image.constant(elevation_range.get('elevation_max')))
  )

  # Normalize the band values to a range from 0 to 1.
  return (
      landsat8.select(config.optical_bands)
      .clamp(config.optical_min, config.optical_max)
      .subtract(config.optical_min)
      .multiply(1.0 / config.optical_max)
      .addBands(
          landsat8.select(config.thermal_bands)
          .clamp(config.thermal_min, config.thermal_max)
          .subtract(config.thermal_min)
          .multiply(1.0 / config.thermal_max)
      )
      .addBands(elevation.select('elevation'))
      .addBands(ee.Image.pixelLonLat().select('latitude').divide(90.0))
  )


def wait_for_task(task_id):
  # Wait until the task finishes.
  status = None
  state = ee.data.getTaskStatus(task_id)[0]['state']
  while state in active_states:
    status = ee.data.getTaskStatus(task_id)[0]
    new_state = status['state']
    if state != new_state:
      state = new_state
      description = status['description'] if 'description' in status else task_id
      logging.info('{}: {}'.format(description, state))
    if state not in active_states:
      break
    time.sleep(1)

  # If it failed, raise an error.
  if state == ee.batch.Task.State.FAILED:
    raise ValueError(status['error_message'])
