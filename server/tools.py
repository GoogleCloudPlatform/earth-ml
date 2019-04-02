import ee
import os
import subprocess as sp

from region_upload import earthengine

EE_PROJECT = os.environ['EE_PROJECT']
EE_IMAGE_COLLECTION = os.environ.get('EE_IMAGE_COLLECTION', 'landcover')


def list_ee_tasks():
  return [
      str(task).lstrip('<').rstrip('>')
      for task in ee.batch.Task.list()
  ]


def clear_image_collections():
  asset_id = '/'.join([EE_PROJECT, EE_IMAGE_COLLECTION])

  outputs = ''
  command = earthengine + ['rm', '-v', '-r', asset_id]
  result = sp.run(command, capture_output=True)
  outputs += f">> {command}\n"
  outputs += f"{result.stdout.decode('utf-8')}"
  outputs += f"stderr: {result.stderr.decode('utf-8')}"
  outputs += "\n\n"

  command = earthengine + ['create', 'collection', asset_id]
  result = sp.run(command, capture_output=True)
  outputs += f">> {command}\n"
  outputs += f"{result.stdout.decode('utf-8')}"
  outputs += f"stderr: {result.stderr.decode('utf-8')}"
  outputs += "\n\n"

  return outputs
