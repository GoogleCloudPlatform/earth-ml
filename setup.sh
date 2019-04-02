#!/bin/bash

: ${EE_PROJECT:?"Please set EE_PROJECT to users/your-ee-username or projects/your-ee-project"}
: ${BUCKET:?"Please set BUCKET to your Cloud Storage bucket (without gs:// prefix)"}

export PROJECT=$(gcloud config get-value project)
export ML_ENGINE_TOPIC='ml-engine'
export REGION_ZOOM_LEVEL=10

# Create the Cloud Storage bucket.
gsutil mb gs://$BUCKET

# Create the Pub/Sub topic and subscription.
gcloud pubsub topics create projects/$PROJECT/topics/$ML_ENGINE_TOPIC
gcloud pubsub subscriptions create projects/$PROJECT/subscriptions/$ML_ENGINE_TOPIC \
  --topic projects/$PROJECT/topics/$ML_ENGINE_TOPIC

# Configure compute engine for Kubernetes.
gcloud config compute/zone us-central1-a
gcloud components install kubectl
gcloud auth configure-docker

CLUSTER=workers-cluster

# Create a Google Kubernetes Engine cluster.
gcloud container clusters create $CLUSTER \
  --enable-autoscaling \
  --min-nodes 1 \
  --max-nodes 50

gcloud container clusters get-credentials $CLUSTER