import ee

import landsat_image


def run(x, y, zoom, year):
  # Return the tile URL for the input landsat image used for classification.
  # mapid = ee.ImageCollection(f"projects/project-earth/landsat_test").getMapId({
  mapid = landsat_image.get(year).getMapId({
      'bands': ['B4', 'B3', 'B2'],
      'min': 0.0,
      'max': 0.3,
      'gamma': 1.5,
  })
  return ee.data.getTileUrl(mapid, x, y, zoom)
