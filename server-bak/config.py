# Google Cloud settings.
project = 'project-earth-2018'
bucket = 'project-earth-2018'
pipeline_topic = 'blocks'

# Earth Engine settings.
ee_project = 'projects/project-earth'
ee_image_collection = 'landcover'
ee_vis_params = {
  'bands': ['B4', 'B3', 'B2'],
  'min': 0.0,
  'max': 0.4,
  'gamma': 1.5,
}

# Band valid value ranges for feature scaling.
optical_bands = ['B1', 'B2', 'B3', 'B4', 'B5', 'B6', 'B7']
optical_min = 0.0
optical_max = 10000.0

thermal_bands = ['B10', 'B11']
thermal_min = 273.15 * 10  # water freezing point in Kelvin.
thermal_max = 373.15 * 10  # water boiling point in Kelvin.

features = optical_bands + thermal_bands
label = 'label'

classifications = [
  {'name': 'Farmland', 'color': 'F0E68C'},
  {'name': 'Forest', 'color': '006400'},
  {'name': 'Grassland', 'color': '9ACD32'},
  {'name': 'Shrublands', 'color': '6B8E23'},
  {'name': 'Wetland', 'color': '66CDAA'},
  {'name': 'Water', 'color': '00BFFF'},
  {'name': 'Tundra', 'color': '40E0D0'},
  {'name': 'Impervious', 'color': '708090'},
  {'name': 'Barren land', 'color': '708090'}, #'F4A460'},
  {'name': 'Snow/Ice', 'color': 'FFFAFA'},
]
palette = [classification['color'] for classification in classifications]

# Constants.
block_zoom = 8  # 4
tile_size = 256
cnn_padding = 16
cnn_patch_size = 2*cnn_padding + 1

# Dataset settings.
dataset_batch_size = 64
dataset_num_parallel_calls = 8

train_files = 8
test_files = 2
train_and_test_files = train_files + test_files

model_file = 'model.h5'