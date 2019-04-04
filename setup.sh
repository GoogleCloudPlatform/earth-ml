#!/bin/bash

# Check the required environment variables.
: ${BUCKET:?"Please set BUCKET to your Cloud Storage bucket (without gs:// prefix)"}
: ${ASSET_ID:?"Please set ASSET_ID to users/your-ee-username/landcover or projects/your-ee-project/landcover"}

export PROJECT=$(gcloud config get-value project)
export ML_ENGINE_TOPIC='ml-engine'

echo "PROJECT=$PROJECT"
echo "BUCKET=$BUCKET"
echo "ASSET_ID=$ASSET_ID"
echo "ML_ENGINE_TOPIC=$ML_ENGINE_TOPIC"

# Create the Cloud Storage bucket.
gsutil mb gs://$BUCKET

# Create the Pub/Sub topic and subscription.
gcloud pubsub topics create projects/$PROJECT/topics/$ML_ENGINE_TOPIC
gcloud pubsub subscriptions create projects/$PROJECT/subscriptions/$ML_ENGINE_TOPIC \
  --topic projects/$PROJECT/topics/$ML_ENGINE_TOPIC

# Configure Compute Engine for Kubernetes.
gcloud config compute/zone us-central1-a
gcloud components install kubectl
gcloud auth configure-docker

# Create a Google Kubernetes Engine cluster with autoscaling.
CLUSTER=workers-cluster
gcloud container clusters create $CLUSTER \
  --enable-autoscaling \
  --min-nodes 1 \
  --max-nodes 50

# Configure kubectl to connect to our newly created cluster.
gcloud container clusters get-credentials $CLUSTER