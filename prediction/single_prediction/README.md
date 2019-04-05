# Single TFRecord Prediction

This directory contains the code that is used to process a single TFRecord file that is exported from Google Earth Engine.

The code in `single_predict.py` uses the following environment variables:

* `INPUT`: GCS path to the input TFRecord file
* `OUTOUT`: GCS path to the output TFRecord file
* `MODELDIR`: GCS path to where the trained model is stored

**Note:** For simplicity, the `Dockerfile` in this directory expects the service account file to be available in this folder, and it will package it up within the docker image. In practice this approach is not recommended and we encourage you to follow the right practices to attach a service account file to your docker container.

### Build the Docker Image

In order to build and register your docker image, you may run the following commands

```bash
export PROJECT_ID=<your-gcp-project>
docker build . -t prediction
docker tag predictor gcr.io/$PROJECT_ID/prediction
docker push gcr.io/$PROJECT_ID/prediction
```