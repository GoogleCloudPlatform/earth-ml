#!/bin/bash

CLUSTER=cluster
GPU_POOL=gpu-pool

IMAGE=dcavazos-test
IMAGE_TAG=latest

PORT=8080

# Print your project settings.
PROJECT_ID=$(gcloud config get-value project)
gcloud config list
echo "GOOGLE_APPLICATION_CREDENTIALS=$GOOGLE_APPLICATION_CREDENTIALS"

# TODO: ask to continue.

# Create a GKE cluster.
if [[ -z $(gcloud container clusters list | egrep "^$CLUSTER") ]]
then
  gcloud container clusters create $CLUSTER \
    --machine-type n1-standard-2 \
    --num-nodes 1 --min-nodes 0 --max-nodes 4 \
    --enable-autoscaling
fi

# Create a GPU node pool.
if [[ -z $(gcloud container node-pools list --cluster $CLUSTER | egrep "^$GPU_POOL") ]]
then
  gcloud container node-pools create $GPU_POOL \
    --cluster $CLUSTER \
    --accelerator type=nvidia-tesla-k80,count=1 \
    --num-nodes 1 --min-nodes 0 --max-nodes 8 \
    --enable-autoscaling
fi

# Configure docker to our project and kubectl to our newly created cluster.
gcloud auth configure-docker
gcloud container clusters get-credentials $CLUSTER

# Build the docker container.
LOCAL_IMAGE=$IMAGE:$IMAGE_TAG
docker build -t $LOCAL_IMAGE .

# Tag the image with a registry name.
GCR_IMAGE=gcr.io/$PROJECT_ID/$IMAGE:$IMAGE_TAG
docker tag $LOCAL_IMAGE $GCR_IMAGE

# Push the image to Container Registry.
docker push $GCR_IMAGE

# Creating the Deployment.
SERVER=$IMAGE
kubectl delete deployment $SERVER
kubectl delete service $SERVER
kubectl run $SERVER --image $GCR_IMAGE --port 80
# kubectl create -f deployment.yaml

# Exposing the Deployment.
kubectl expose deployment $SERVER \
  --type LoadBalancer --port 80 --target-port $PORT

# Inspecting the application.
kubectl get service $SERVER_NAME
