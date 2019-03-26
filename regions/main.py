import argparse
import json
import logging
import random
import requests
import sys
import time

import apache_beam as beam
from apache_beam.options.pipeline_options import GoogleCloudOptions
from apache_beam.options.pipeline_options import PipelineOptions

# Default values.
default_local_rest_api_url = 'http://127.0.0.1:4201'
default_rest_api_url = 'https://rest-api-dot-project-earth-2018.appspot.com'
default_prediction_url = 'https://us-central1-project-earth-2018.cloudfunctions.net/BatchPredict3'
default_ee_image_collection = 'landcover'
default_regions_subscription = 'regions'
default_predictions_subscription = 'predictions'


def parse_json_region(json_region):
  try:
    # Parse the JSON region data.
    data = json.loads(json_region)
    region = {
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
      value = region[field]
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
    logging.info('Processing region {}'.format(region['id']))
    yield region

  except Exception as e:
    logging.error('{} (json_region={})'.format(e, repr(json_region)))
    return


def run_with_retries(function, retries=0):
  for i in range(retries+1):
    try:
      yield function()
      return
    except Exception as e:
      logging.error('{} params={}'.format(e, repr(params)))

      # Exponential backoff
      retry_wait = min(2**i, 60) + random.random()
      logging.error('Retrying in {} seconds ({} of {})'.format(
          retry_wait, i+1, retries+1))
      time.sleep(retry_wait)



def request(params, url, **kwargs):
  params.update(kwargs)
  def try_request():
    logging.info('GET {} {}'.format(url, params))
    r = requests.get(url, params)
    r.raise_for_status()
    return r.json()
  for result in run_with_retries(try_request):
    yield result


# import requests, main; url = main.default_prediction_url; params = main.params
# r = requests.get(url, params); r.raise_for_status()
params = {
  'region_id': '328-790-2014',
  'input_path': 'gs://project-earth-regions/328/790/2014.tfrecord.gz',
  'output_path': 'gs://project-earth-classifications/328/790/2014',
}
def run_prediction(params, url):
  def try_run_prediction():
    predict_params = {
      'input_path': params['inputs_file'],
      'output_path': params['classifications_file'],
    }
    logging.info('GET {} {}'.format(url, predict_params))
    r = requests.get(url, predict_params)
    r.raise_for_status()
    return params
  for result in run_with_retries(try_run_prediction):
    yield result


def run(
    pipeline_args,
    prediction_url=default_prediction_url,
    regions_subscription=default_regions_subscription,
    predictions_subscription=default_predictions_subscription,
):
  pubsub_id_label = None
  rest_api_url = default_local_rest_api_url
  for i, arg in enumerate(pipeline_args):
    if arg == '--runner' and i+1 < len(pipeline_args) and \
        'dataflow' in pipeline_args[i+1].lower():
      pubsub_id_label = 'id'
      rest_api_url = default_rest_api_url

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

  def subscription_path(subscription):
    return 'projects/{}/subscriptions/{}'.format(project, subscription)
  print(subscription_path(regions_subscription))
  with beam.Pipeline(options=options) as pipeline:
    # Run the region processing pipeline.
    (
        pipeline
        | 'Read regions' >> beam.io.ReadFromPubSub(
            subscription=subscription_path(regions_subscription),
            id_label=pubsub_id_label,
        )
        | 'Parse JSON region' >> beam.ParDo(parse_json_region)
        | 'Request EE image' >> beam.ParDo(
            request, rest_api_url + '/landsat/region')
        | 'Model predict' >> beam.ParDo(run_prediction, prediction_url)
    )

    # Once the predictions are ready, upload them back to Earth Engine.
    (
        'Read regions' >> beam.io.ReadFromPubSub(
            subscription=subscription_path(predictions_subscription)
        )
        # | 'Parse JSON predictions' >> beam.ParDo(parse_json_region)
        | 'Upload EE asset' >> beam.ParDo(
            request, rest_api_url + '/landcover/upload')
    )


if __name__ == '__main__':
  # Set the logging options.
  logging.basicConfig(
    format='%(filename)s:%(funcName)s:%(lineno)s: %(message)s',
    level=logging.INFO,
  )

  parser = argparse.ArgumentParser()
  # Optional arguments.
  parser.add_argument(
      '--rest-api-url',
      type=str,
      default=default_rest_api_url,
  )
  parser.add_argument(
      '--prediction-url',
      type=str,
      default=default_prediction_url,
  )
  parser.add_argument(
      '--regions-subscription',
      type=str,
      default=default_regions_subscription,
  )
  parser.add_argument(
      '--predictions-subscription',
      type=str,
      default=default_predictions_subscription,
  )
  args, pipeline_args = parser.parse_known_args()

  run(
      pipeline_args=pipeline_args,
      prediction_url=args.prediction_url,
      regions_subscription=args.regions_subscription,
      predictions_subscription=args.predictions_subscription,
  )
