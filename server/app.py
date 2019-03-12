import flask
import json
import logging

import ee_asset
import ee_landsat8
import model

import tensorflow as tf
tf.enable_eager_execution()

app = flask.Flask(__name__)

# Set the logging options.
logging.basicConfig(
    format="[%(levelname)s] %(asctime)-15s %(funcName)s: %(message)s",
    level=logging.INFO,
)


@app.route('/')
def index():
  return ''


@app.route('/landcover/<int:x>/<int:y>/<int:zoom>/<int:year>')
def landcover_tile_url(x, y, zoom, year):
  return flask.redirect(ee_asset.tile_url(x, y, zoom, year))


@app.route('/landsat8/<int:x>/<int:y>/<int:zoom>/<int:year>')
def landsat8_tile_url(x, y, zoom, year):
  return flask.redirect(ee_landsat8.tile_url(x, y, zoom, year))


@app.route('/landsat8/request')
def landsat8_request():
  args = flask.request.args
  return json.dumps(ee_landsat8.request(
      block_id=args['id'],
      x=int(args['x']),
      y=int(args['y']),
      year=int(args['year']),
      north=float(args['north']),
      east=float(args['east']),
      south=float(args['south']),
      west=float(args['west']),
      bucket=args['bucket'],
  ))


@app.route('/landsat8/wait')
def landsat8_wait():
  args = flask.request.args
  return json.dumps(ee_landsat8.wait(
      block_id=args['id'],
      task_id=args['task_id'],
      file_prefix=args['file_prefix'],
  ))


@app.route('/model/predict')
def model_predict():
  args = flask.request.args
  return json.dumps(model.predict(
      block_id=args['id'],
      inputs_file=args['inputs_file'],
      mixer_file=args['mixer_file'],
      predictions_file=args['predictions_file'],
  ))


@app.route('/asset/upload')
def asset_upload():
  args = flask.request.args
  return json.dumps(ee_asset.upload(
      block_id=args['id'],
      predictions_file=args['predictions_file'],
      mixer_file=args['mixer_file'],
  ))


if __name__ == '__main__':
  app.run(host='127.0.0.1', port=4213, debug=True)
