# Project Earth

## Setup

```sh
export BUCKET='your-cloud-storage-bucket'
export EE_PROJECT='users/your-ee-username'  # or 'projects/your-ee-project'
```

```sh
export PROJECT=$(gcloud config get-value project)
export ML_ENGINE_TOPIC='ml-engine'
```

```sh
# To test locally, it is recommended to use a small region size.
export REGION_ZOOM_LEVEL=8  # world subdivided into 2^8 * 2^8 = 65536 regions (smaller)

# A larger region size would be suitable for production environments.
# export REGION_ZOOM_LEVEL=4  # world subdivided into 2^4 * 2^4 = 256 regions (larger)
```

## Development environment

Before you start, make sure you have the following installed:
* [Google Cloud SDK](https://cloud.google.com/sdk/install)
* [Docker](https://docs.docker.com/install/)
* [Python 3](https://www.python.org/downloads/) (3.6 or higher)

Test your development environment.

```sh
gcloud version
docker --version
python3 --version
```

---

# Creating Google Cloud resources

```sh
# Create the Cloud Storage bucket.
gsutil mb gs://$BUCKET

# Create the Pub/Sub topic and subscription.
gcloud pubsub topics create projects/$PROJECT/topics/$ML_ENGINE_TOPIC
gcloud pubsub subscriptions create projects/$PROJECT/subscriptions/$ML_ENGINE_TOPIC \
  --topic projects/$PROJECT/topics/$ML_ENGINE_TOPIC
```

---

## Deploying the web app and server to App Engine

```sh
( cd webapp ; ng build --prod )
gcloud app deploy webapp
gcloud app deploy server
```

```sh
export SERVER="https://server-dot-$PROJECT.appspot.com"
```

## Deploying the Cloud Functions dispatcher

```sh
( cd dispatch ; gcloud functions deploy dispatch \
  --runtime python37 \
  --trigger-bucket $BUCKET \
  --set-env-vars PROJECT=$PROJECT,SERVER=$SERVER,ML_ENGINE_TOPIC=$ML_ENGINE_TOPIC )
```

## Configuring the backend cluster

```sh
gcloud config compute/zone us-central1-a
gcloud components install kubectl
gcloud auth configure-docker

DEPLOYMENT=workers
CLUSTER=$DEPLOYMENT-cluster
IMAGE=gcr.io/$PROJECT/$DEPLOYMENT:latest

# Create a Google Kubernetes Engine cluster.
gcloud container clusters create $CLUSTER \
  --enable-autoscaling \
  --min-nodes 1 \
  --max-nodes 50

gcloud container clusters get-credentials $CLUSTER

# Build and push the docker container.
docker build -t $IMAGE worker/
docker push $IMAGE

# Create a new Deployment to run the service.
kubectl run $DEPLOYMENT --image $IMAGE

kubectl autoscale deployment $DEPLOYMENT \
  --min 1 --max 50 --cpu-percent 80
```

Inspecting the cluster deployment.
```sh
kubectl get deployment $DEPLOYMENT
kubectl get pods
```

To update the service's image.
```sh
kubectl set image deployment/$DEPLOYMENT $DEPLOYMENT=$IMAGE
```

---
```sh
# Started at 12:13am
curl -X GET "$SERVER/region/extract/40/98/2018"
curl -X GET "$SERVER/region/extract/40/99/2018"
curl -X GET "$SERVER/region/extract/40/100/2018"
curl -X GET "$SERVER/region/extract/41/98/2018"
# curl -X GET "$SERVER/region/extract/41/99/2018"
curl -X GET "$SERVER/region/extract/41/100/2018"
curl -X GET "$SERVER/region/extract/42/98/2018"
curl -X GET "$SERVER/region/extract/42/99/2018"
curl -X GET "$SERVER/region/extract/42/100/2018"
# Last classification eneded at 12:45:50
python dispatch/main.py "gs://earth-dummy/landcover/40/98/2018/00000.tfrecord"
python dispatch/main.py "gs://earth-dummy/landcover/40/99/2018/00000.tfrecord"
python dispatch/main.py "gs://earth-dummy/landcover/40/100/2018/00000.tfrecord"
python dispatch/main.py "gs://earth-dummy/landcover/41/98/2018/00000.tfrecord"
python dispatch/main.py "gs://earth-dummy/landcover/41/99/2018/00000.tfrecord"
python dispatch/main.py "gs://earth-dummy/landcover/41/100/2018/00000.tfrecord"
python dispatch/main.py "gs://earth-dummy/landcover/42/98/2018/00000.tfrecord"
python dispatch/main.py "gs://earth-dummy/landcover/42/99/2018/00000.tfrecord"
python dispatch/main.py "gs://earth-dummy/landcover/42/100/2018/00000.tfrecord"
# Upload started at 9:16
# Upload ended at 9:23
```

# Processing a region

```sh
curl -X GET "$SERVER"
```

### Classifying the region

```sh
curl -X GET "$SERVER/region/classify/20/49/2018"
```

```sh
YEAR=2018

# California
curl -X GET "$SERVER/submit/bounds/$YEAR?west=-125.8935&south=32.48171&east=-114.1291&north=42.01618"

# United States
curl -X GET "$SERVER/submit/bounds/$YEAR?west=-125.3321&south=23.8991&east=-65.7421&north=49.4325"

# Planet
curl -X GET "$SERVER/submit/bounds/$YEAR?west=-180&south=-90&east=180&north=90"
```

To check more bounds by area, you can check [OpenMapTiles](https://openmaptiles.com/downloads/planet/).
The bounds are specified as `west, south, east, north`.

```sh
# To show more details on the job.
gcloud ml-engine jobs describe <JOB_ID>

# To cancel a job.
gcloud ml-engine jobs cancel <JOB_ID>
```

Once the job reaches status `SUCCEEDED`, you'll be able to check the results.
```sh
gsutil ls -lh gs://$BUCKET/ml-engine/20/49/2018
```

### Transforming ML Engine results to TFRecord

```sh
gcloud pubsub topics publish $ML_ENGINE_TOPIC \
  --message "gs://$BUCKET/ml-engine/21/49/2013/prediction.results-00000-of-00006"
gcloud pubsub topics publish $ML_ENGINE_TOPIC \
  --message "gs://$BUCKET/ml-engine/21/49/2013/prediction.results-00001-of-00006"
gcloud pubsub topics publish $ML_ENGINE_TOPIC \
  --message "gs://$BUCKET/ml-engine/21/49/2013/prediction.results-00002-of-00006"
gcloud pubsub topics publish $ML_ENGINE_TOPIC \
  --message "gs://$BUCKET/ml-engine/21/49/2013/prediction.results-00003-of-00006"
gcloud pubsub topics publish $ML_ENGINE_TOPIC \
  --message "gs://$BUCKET/ml-engine/21/49/2013/prediction.results-00004-of-00006"
gcloud pubsub topics publish $ML_ENGINE_TOPIC \
  --message "gs://$BUCKET/ml-engine/21/49/2013/prediction.results-00005-of-00006"
```

### Uploading to Earth Engine

```sh
curl -X GET "$SERVER/region/upload/20/49/2018"
```

# Job dispatcher with Cloud Storage triggers

# Web Application

## Option A: Running locally

```sh
( cd webapp ; ng serve )
```

## Option B: Deploying to App Engine

```sh
( cd webapp ; ng build --prod )
gcloud app deploy webapp
```