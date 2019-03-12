import argparse
import json
import logging
import requests
import sys

import apache_beam as beam
from apache_beam.options.pipeline_options import GoogleCloudOptions
from apache_beam.options.pipeline_options import PipelineOptions

# Default values.
default_server = 'http://127.0.0.1:4213'
default_ee_image_collection = 'landcover'
default_blocks_subscription = 'blocks'

# Set the logging options.
logging.basicConfig(
    format="[%(levelname)s] %(asctime)-15s %(funcName)s: %(message)s",
    level=logging.INFO,
)


def parse_json_block(json_block):
  try:
    # Parse the JSON block data.
    data = json.loads(json_block)
    block = {
        'id': data['id'],
        'x': data['x'],
        'y': data['y'],
        'year': data['year'],
        'north': data['north'],
        'east': data['east'],
        'south': data['south'],
        'west': data['west'],
    }

    # Validate the values for the rest of the pipeline.
    def validate(field, dtype):
      value = block[field]
      assert isinstance(value, dtype), "expected {}, got {} ({}={})".format(
          dtype, type(value), field, repr(value))
    validate('id', (str, unicode))
    validate('x', int)
    validate('y', int)
    validate('year', int)
    validate('north', float)
    validate('east', float)
    validate('south', float)
    validate('west', float)
    logging.info('Processing block {}'.format(block['id']))
    yield block

  except Exception as e:
    logging.error('{} (json_block={})'.format(e, repr(json_block)))
    return


# TODO: add 3 retries with exponential backoff.
def request(params, url, **kwargs):
  logging.info('GET {} {}'.format(url, params))
  params.update(kwargs)
  try:
    r = requests.get(url, params)
    r.raise_for_status()
    yield r.json()
  except Exception as e:
    logging.error('{} (params={}, url={})'.format(e, repr(params), repr(url)))


def run(
    pipeline_args,
    bucket,
    server=default_server,
    blocks_subscription=default_blocks_subscription,
):
  options = PipelineOptions(
      pipeline_args,
      save_main_session=True,
      streaming=True,
  )
  project = options.view_as(GoogleCloudOptions).project
  if project is None:
    parser.print_usage()
    print(sys.argv[0] + ': error: argument --project is required')
    sys.exit(1)

  with beam.Pipeline(options=options) as pipeline:
    (
        pipeline
        | 'Read blocks' >> beam.io.ReadFromPubSub(
          subscription='projects/{}/subscriptions/{}'.format(
              project, blocks_subscription),
          id_label='id',
        )
        | 'Parse JSON block' >> beam.ParDo(parse_json_block)
        | 'Request EE image' >> beam.ParDo(request, server + '/landsat8/request', bucket=bucket)
        | 'Wait for EE image' >> beam.ParDo(request, server + '/landsat8/wait')
        | 'Model predict' >> beam.ParDo(request, server + '/model/predict')
        | 'Upload EE asset' >> beam.ParDo(request, server + '/asset/upload')
    )


if __name__ == '__main__':
  parser = argparse.ArgumentParser()
  # Mandatory arguments.
  parser.add_argument(
      '--bucket',
      type=str,
      required=True,
  )

  # Optional arguments.
  parser.add_argument(
      '--server',
      type=str,
      default=default_server,
  )
  parser.add_argument(
      '--blocks-subscription',
      type=str,
      default=default_blocks_subscription,
  )
  args, pipeline_args = parser.parse_known_args()

  run(
      pipeline_args=pipeline_args,
      bucket=args.bucket,
      server=args.server,
      blocks_subscription=args.blocks_subscription,
  )
