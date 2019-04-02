import ee
import flask
import json
import os

import tools
import tile_landsat
import tile_landcover
import region_classify
import region_upload
import submit

app = flask.Flask(__name__)

# Initialize Earth Engine.
credentials_file = os.environ['GOOGLE_APPLICATION_CREDENTIALS']
with open(credentials_file) as f:
  credentials = json.load(f)
  credentials_email = credentials['client_email']
ee.Initialize(ee.ServiceAccountCredentials(credentials_email, credentials_file))


@app.route('/')
def index():
  return flask.render_template('index.html', zoom_level=submit.REGION_ZOOM_LEVEL)


#===--- tools ---===#
@app.route('/list-ee-tasks')
def app_list_ee_tasks():
  result = dump(tools.list_ee_tasks(), pretty=True)
  return f"""<pre>{result}</pre><a href="/">Go back</a>"""


@app.route('/clear-image-collection')
def app_clear_image_collection():
  result = tools.clear_image_collections()
  return f"""<pre>{result}</pre><a href="/">Go back</a>"""


#===--- tile --===#
@app.route('/tile/landsat/<int:x>/<int:y>/<int:zoom>/<int:year>')
def app_tile_landsat(x, y, zoom, year):
  return flask.redirect(tile_landsat.run(x, y, zoom, year))


@app.route('/tile/landcover/<int:x>/<int:y>/<int:zoom>/<int:year>')
def app_tile_landcover(x, y, zoom, year):
  return flask.redirect(tile_landcover.run(x, y, zoom, year))


#===--- region ---===#
@app.route('/region/classify', methods=['POST'])
def app_region_classify():
  args = flask.request.args
  return dump(region_classify.run(
      x=int(args['x']),
      y=int(args['y']),
      year=int(args['year']),
      part=int(args['part']),
  ))


@app.route('/region/upload', methods=['POST'])
def app_region_upload():
  args = flask.request.args
  return dump(region_upload.run(
      x=int(args['x']),
      y=int(args['y']),
      year=int(args['year']),
      parts=int(args['parts']),
  ))


#===--- submit ---===#
@app.route('/submit/region', methods=['POST'])
def app_extract_point():
  args = flask.request.args
  return dump(submit.region(
      x=int(args['x']),
      y=int(args['y']),
      start_year=int(args['start_year']),
      end_year=int(args['end_year']),
  ))


@app.route('/submit/point', methods=['POST'])
def app_submit_point():
  args = flask.request.form
  return dump(submit.point(
      lng=float(args['lng']),
      lat=float(args['lat']),
      start_year=int(args['start_year']),
      end_year=int(args['end_year']),
  ))


@app.route('/submit/bounds', methods=['POST'])
def app_submit_bounds():
  args = flask.request.args
  return dump(submit.bounds(
      west=float(args['west']),
      south=float(args['south']),
      east=float(args['east']),
      north=float(args['north']),
      start_year=int(args['start_year']),
      end_year=int(args['end_year']),
  ))


@app.route('/submit/tile', methods=['POST'])
def app_submit_tile(x, y, zoom, year):
  args = flask.request.args
  return dump(submit.tile(
      x=int(args['x']),
      y=int(args['y']),
      zoom=int(args['zoom']),
      start_year=int(args['start_year']),
      end_year=int(args['end_year']),
  ))


#===--- helper functions ---===#
def as_bool(string_value):
  return string_value.lower() in ('y', 'yes', 't', 'true', '1'),


def dump(data, pretty=False):
  if pretty:
    return json.dumps(data, indent=2, separators=(', ', ': '))
  return json.dumps(data, separators=(',', ':'))


if __name__ == '__main__':
  app.run(host='127.0.0.1', debug=True)
