#!/bin/bash

# Check the required environment variables.
: ${PROJECT:?"Please set PROJECT to your Google Cloud Project ID"}
: ${BUCKET:?"Please set BUCKET to your Cloud Storage bucket (without gs:// prefix)"}
: ${ML_ENGINE_TOPIC:?"Please set ML_ENGINE_TOPIC to a PubSub topic"}

# Deploying the Cloud Functions dispatcher.
( cd dispatch ; gcloud functions deploy dispatch \
  --runtime python37 \
  --memory 2048MB \
  --timeout 540s \
  --trigger-bucket $BUCKET \
  --set-env-vars PROJECT=$PROJECT,ML_ENGINE_TOPIC=$ML_ENGINE_TOPIC )
