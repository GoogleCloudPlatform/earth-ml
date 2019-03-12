#!/bin/bash

CLUSTER_NAME=cluster
GPU_POOL_NAME=gpu-pool

IMAGE_NAME=dcavazos-test
IMAGE_TAG=latest

PORT=8080

# Print your project settings.
PROJECT_ID=$(gcloud config get-value project)
gcloud config list
echo "GOOGLE_APPLICATION_CREDENTIALS=$GOOGLE_APPLICATION_CREDENTIALS"

# TODO: ask to continue.

# Create a GKE cluster.
if [[ -z $(gcloud container clusters list | egrep "^$CLUSTER_NAME") ]]
then
  gcloud container clusters create $CLUSTER_NAME \
    --machine-type n1-standard-2 \
    --num-nodes 1 --min-nodes 0 --max-nodes 4 \
    --enable-autoscaling
fi

# Create a GPU node pool.
if [[ -z $(gcloud container node-pools list --cluster $CLUSTER_NAME | egrep "^$GPU_POOL_NAME") ]]
then
  gcloud container node-pools create $GPU_POOL_NAME \
    --cluster $CLUSTER_NAME \
    --accelerator type=nvidia-tesla-k80,count=1 \
    --num-nodes 1 --min-nodes 0 --max-nodes 8 \
    --enable-autoscaling
fi

# Build the docker container.
LOCAL_IMAGE=$IMAGE_NAME:$IMAGE_TAG
docker build -t $LOCAL_IMAGE .

# Tag the image with a registry name.
GCR_IMAGE=gcr.io/$PROJECT_ID/$IMAGE_NAME:$IMAGE_TAG
docker tag $LOCAL_IMAGE $GCR_IMAGE

# Push the image to Container Registry.
docker push $GCR_IMAGE

# Creating the Deployment.
SERVER_NAME=$IMAGE_NAME
kubectl delete deployment $SERVER_NAME
kubectl delete service $SERVER_NAME
# kubectl run $SERVER_NAME --image $GCR_IMAGE --port 80
kubectl create -f deployment.yaml

# Exposing the Deployment.
kubectl expose deployment $SERVER_NAME --type LoadBalancer \
  --port 80 --target-port $PORT

# Inspecting the application.
kubectl get service $SERVER_NAME
