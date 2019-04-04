import ee
import json
import os
from google.cloud import storage

# Environment variables.
PROJECT = os.environ['PROJECT']
BUCKET = os.environ['BUCKET']
ASSET_ID = os.environ['ASSET_ID']
CREDENTIALS_FILE = os.environ['GOOGLE_APPLICATION_CREDENTIALS']

# Constants.
region_zoom_level = 6

# Initialize Earth Engine.
with open(CREDENTIALS_FILE) as f:
  credentials = json.load(f)
  credentials_email = credentials['client_email']
ee.Initialize(ee.ServiceAccountCredentials(credentials_email, CREDENTIALS_FILE))

earthengine = ['earthengine', '--service_account_file', CREDENTIALS_FILE]

# Initialize the Google Cloud client libraries.
storage_client = storage.Client()
bucket = storage_client.bucket(BUCKET)
