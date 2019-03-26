import flask
import json
import logging
import requests

import landcover
import landsat
import uploader

app = flask.Flask(__name__)


@app.route('/')
def index():
  return ':)'


#==-- Landsat --==#
@app.route('/landsat/tile/<int:x>/<int:y>/<int:zoom>/<int:year>')
def landsat_tile(x, y, zoom, year):
  return flask.redirect(landsat.tile(x, y, zoom, year))


@app.route('/landsat/region')
def landsat_region():
  args = flask.request.args
  return json.dumps(landsat.region(
      region_id=args['id'],
      x=int(args['x']),
      y=int(args['y']),
      year=int(args['year']),
      north=float(args['north']),
      east=float(args['east']),
      south=float(args['south']),
      west=float(args['west']),
  ))


#==-- Landcover --==#
@app.route('/landcover/tile/<int:x>/<int:y>/<int:zoom>/<int:year>')
def landcover_tile(x, y, zoom, year):
  return flask.redirect(landcover.tile(x, y, zoom, year))


@app.route('/landcover/classify')
def landcover_classify():
  args = flask.request.args
  return json.dumps(classifier.classify(
      region_id=args['id'],
      inputs_file=args['inputs_file'],
      mixer_file=args['mixer_file'],
      classifications_file=args['classifications_file'],
  ))


@app.route('/landcover/upload')
def landcover_upload():
  args = flask.request.args
  return json.dumps(uploader.upload(
      region_id=args['id'],
      classifications_file=args['classifications_file'],
      mixer_file=args['mixer_file'],
  ))


if __name__ == '__main__':
  # Set the logging options.
  logging.basicConfig(
    format='%(filename)s:%(funcName)s:%(lineno)s: %(message)s',
    level=logging.INFO,
  )

  app.run(host='127.0.0.1', port=4201, threaded=True, debug=True)
