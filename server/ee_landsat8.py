import ee
import logging
import time

import config

# Initialize Earth Engine.
ee.Initialize()


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
  # Start the task asynchronously to export to Google Cloud Storage.
  file_prefix = 'blocks/{}/{}/{}'.format(x, y, year)

  task = ee.batch.Export.image.toCloudStorage(
      image=get_image(year),
      description=block_id,
      bucket=bucket,
      fileNamePrefix=file_prefix,
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

  logging.info('{}: ee_request.image done'.format(block_id))
  return {
      'id': block_id,
      'task_id': task.id,
      'file_prefix': 'gs://{}/{}'.format(bucket, file_prefix),
  }


def wait(block_id, task_id, file_prefix):
  active_states = (
      None,
      ee.batch.Task.State.READY,
      ee.batch.Task.State.RUNNING,
  )

  # Wait until the task finishes.
  status = None
  state = None
  while state in active_states:
    status = ee.data.getTaskStatus(task_id)[0]
    new_state = status['state']
    if state != new_state:
      state = new_state
      if 'description' in status:
        logging.info('{}: {}'.format(block_id, state))
    if state not in active_states:
      break
    time.sleep(1)

  # If it failed, raise an error.
  if state == ee.batch.Task.State.FAILED:
    raise ValueError(status['error_message'])

  logging.info('{}: EE task {}, state={}'.format(block_id, task_id, state))
  return {
      'id': block_id,
      'inputs_file': file_prefix + '.tfrecord.gz',
      'mixer_file': file_prefix + '.json',
      'predictions_file': file_prefix + '.predictions.tfrecord',
  }
