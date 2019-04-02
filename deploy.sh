#!/bin/bash

: ${GOOGLE_APPLICATION_CREDENTIALS:?"Please set GOOGLE_APPLICATION_CREDENTIALS to your service account credentials json file"}
: ${EE_PROJECT:?"Please set EE_PROJECT to users/your-ee-username or projects/your-ee-project"}
: ${BUCKET:?"Please set GCS_BUCKET to your Cloud Storage bucket (without gs:// prefix)"}

export PROJECT=$(gcloud config get-value project)
export ML_ENGINE_TOPIC='ml-engine'
export REGION_ZOOM_LEVEL=10

# Generate the server's App Engine yaml file with the environment variables.
cat > server/app.yaml <<EOF
runtime: python37
service: server
env_variables:
  GOOGLE_APPLICATION_CREDENTIALS: $GOOGLE_APPLICATION_CREDENTIALS
  PROJECT: $PROJECT
  BUCKET: $BUCKET
  EE_PROJECT: $EE_PROJECT
  REGION_ZOOM_LEVEL: $REGION_ZOOM_LEVEL
EOF

# Deploying the web app and the server.
( cd webapp ; ng build --prod )
gcloud app deploy webapp server

export SERVER="https://server-dot-$PROJECT.appspot.com"

# Deploying the Cloud Functions dispatcher.
( cd dispatch ; gcloud functions deploy dispatch \
  --runtime python37 \
  --trigger-bucket $BUCKET \
  --set-env-vars PROJECT=$PROJECT,SERVER=$SERVER,ML_ENGINE_TOPIC=$ML_ENGINE_TOPIC )

# Build and push the docker container.
DEPLOYMENT=workers
IMAGE=gcr.io/$PROJECT/$DEPLOYMENT:latest

docker build -t $IMAGE worker/
docker push $IMAGE

# Create a new Deployment to run the service and autoscale it.
kubectl delete deployment $DEPLOYMENT
kubectl run $DEPLOYMENT --image $IMAGE
kubectl autoscale deployment $DEPLOYMENT \
  --min 1 --max 50 --cpu-percent 80
