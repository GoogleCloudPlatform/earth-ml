#!/bin/bash

# Check the required environment variables.
: ${BUCKET:?"Please set BUCKET to your Cloud Storage bucket (without gs:// prefix)"}
# : ${ML_ENGINE_TOPIC:?"Please set ML_ENGINE_TOPIC to a PubSub topic"}
: ${ASSET_ID:?"Please set ASSET_ID to users/your-ee-username/landcover or projects/your-ee-project/landcover"}
: ${GOOGLE_APPLICATION_CREDENTIALS:?"Please set GOOGLE_APPLICATION_CREDENTIALS to point to the path/to/your/credentials.json"}

export PROJECT=$(gcloud config get-value project)

echo "PROJECT=$PROJECT"
echo "BUCKET=$BUCKET"
# echo "ML_ENGINE_TOPIC=$ML_ENGINE_TOPIC"
echo "ASSET_ID=$ASSET_ID"
echo "GOOGLE_APPLICATION_CREDENTIALS=$GOOGLE_APPLICATION_CREDENTIALS"

# Deploy the web application to App Engine.
bash webapp/deploy.sh

# Deploy the server to App Engine.
bash server/deploy.sh

# Deploy the dispatcher to Cloud Functions.
bash dispatch/deploy.sh

# Deploy the workers to Kubernetes.
# bash worker/deploy.sh
