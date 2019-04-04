import ee
import os

import config

# Model classifications with the palette for visualization.
classifications = [
    {'color': 'fbc02d', 'name': 'Farmland'},    # Yellow 700
    {'color': '689f38', 'name': 'Forest'},      # Light Green 600
    {'color': 'aed581', 'name': 'Grassland'},   # Light Green 300
    {'color': 'e6ee9c', 'name': 'Shrublands'},  # Lime 200
    {'color': '26a69a', 'name': 'Wetland'},     # Teal 400
    {'color': '90caf9', 'name': 'Water'},       # Blue 200
    {'color': 'ffab91', 'name': 'Tundra'},      # Deep Orange 200
    {'color': 'e0e0e0', 'name': 'Impervious'},  # Gray 300
    {'color': 'ffecb3', 'name': 'Barren land'}, # Amber 100
    {'color': 'fafafa', 'name': 'Snow/Ice'},    # Gray 50
]
palette = [classification['color'] for classification in classifications]

def run(tile_x, tile_y, zoom, year):
  # Return the tile URL for the landcover ImageCollection.
  mapid = (
      ee.ImageCollection(config.ASSET_ID)
      .filterDate(f"{year}-1-1", f"{year}-12-31")
      .getMapId({
          'min': 0.0,
          'max': len(classifications)-1,
          'palette': palette,
      })
  )
  return ee.data.getTileUrl(mapid, tile_x, tile_y, zoom)
