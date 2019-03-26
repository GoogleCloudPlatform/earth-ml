import ee
import logging
import time

import cache
import config

# Initialize Earth Engine.
ee.Initialize()

active_states = (
    ee.batch.Task.State.READY,
    ee.batch.Task.State.RUNNING,
)


def get_image(year):
  def mask_clouds(image):
    qa = image.select('pixel_qa')
    return image.updateMask(
        qa.bitwiseAnd(1 << 3).eq(0)       # Cloud shadow bit
        .And(qa.bitwiseAnd(1 << 5).eq(0))  # Cloud bit
    )

  start_year = ee.Number(year).subtract(1)
  start_date = ee.Date.fromYMD(start_year, 1, 1)  # pylint: disable=no-member
  end_date = ee.Date.fromYMD(year, 1, 1)          # pylint: disable=no-member

  image = (
      ee.ImageCollection('LANDSAT/LC08/C01/T1_SR')
      .filterDate(start_date, end_date)
      .map(mask_clouds)
      .median()
  )

  # Normalize the band values to a range from 0 to 1.
  return (
      image.select(config.optical_bands)
      .clamp(config.optical_min, config.optical_max)
      .subtract(config.optical_min)
      .multiply(1.0 / config.optical_max)
      .addBands(
          image.select(config.thermal_bands)
          .clamp(config.thermal_min, config.thermal_max)
          .subtract(config.thermal_min)
          .multiply(1.0 / config.thermal_max)
      )
  )


def tile_url(x, y, zoom, year):
  mapid = get_image(year).getMapId(config.ee_vis_params)
  return ee.data.getTileUrl(mapid, x, y, zoom)


def request(block_id, x, y, year, north, east, south, west, bucket):
  prefix = 'blocks/{}/{}/{}'.format(x, y, year)
  file_prefix = 'gs://{}/{}'.format(bucket, prefix)
  inputs_file = file_prefix + '.tfrecord.gz'
  mixer_file = file_prefix + '.json'
  predictions_file = file_prefix + '.predictions.tfrecord'
  result = {
    'id': block_id,
    'inputs_file': inputs_file,
    'mixer_file': mixer_file,
    'predictions_file': predictions_file,
  }

  if cache.gcs_file_exists(inputs_file) and cache.gcs_file_exists(inputs_file):
    logging.info('{}: found {}'.format(block_id, inputs_file))
    return result
  
  task_id = None
  if block_id in cache.blocks:
    cached_block = cache.blocks[block_id]
    if 'task_id' in cached_block:
      task_id = cached_block['task_id']
      if ee.data.getTaskStatus(task_id)[0] not in active_states:
        task_id = None

  if task_id is None:
    # Start the task asynchronously to export to Google Cloud Storage.
    task = ee.batch.Export.image.toCloudStorage(
        image=get_image(year),
        description=block_id,
        bucket=bucket,
        fileNamePrefix=prefix,
        region=[
            [east, north],
            [west, north],
            [west, south],
            [east, south],
            [east, north],
        ],
        scale=30,
        fileFormat='TFRecord',
        formatOptions={
            'patchDimensions': [config.tile_size, config.tile_size],
            'kernelSize': [config.cnn_patch_size, config.cnn_patch_size],
            'compressed': True,
        },
    )
    task.start()

    task_id = task.id
    cache.blocks.update_fields(block_id, {
      'task_id': task_id,
    })
    logging.info('{}: started task {}'.format(block_id, task_id))

  wait_for_task(task_id)
  return result


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
