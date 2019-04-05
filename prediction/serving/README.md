# Serving the Model

This directory contains the code to create a flask server  to create prediction jobs on a Kubernetes cluster.

The code in `service.py` uses the following endpoints:

* `process`: a POST request which takes a jso object with 3 keys:
  * `input`: GCS path to the input TFRecord file
  * `output`: GCS path to the output TFRecord file
  * `name`: The job name on kubernetes
* `list`: a GET request with no parameters. It returns a list of all created jobs
* `delete`: a GET request with no parameters. It deletes all the created jobs, whether they are completed or not.

**Note:** For simplicity, the `Dockerfile` in this directory expects the service account file to be available in this folder, and it will package it up within the docker image. In practice this approach is not recommended and we encourage you to follow the right practices to attach a service account file to your docker container.

### Build the Docker Image

In order to build and register your docker image, you may run the following commands

```bash
export PROJECT_ID=<your-gcp-project>
docker build . -t earth-server
docker tag earth-server gcr.io/$PROJECT_ID/earth-server
docker push gcr.io/$PROJECT_ID/earth-server
```

### Create the Service

To create an endpoint in your kubernetes cluster:

```bash
kubectl run landcover-predictor --image=gcr.io/$PROJECT_ID/earth-server --port 5000 -n kubeflow
kubectl expose deployment landcover-predictor --type=LoadBalancer --port 7070 --target-port 5000 -n kubeflow
```

Once the endpoint is created, you may find the IP address on the kubernetes cluster page (under Services).

### Updating the Service

To update the served docker image:
```bash
kubectl set image deployment/landcover-predictor landcover-predictor=gcr.io/$PROJECT_ID/earth-server:v2 -n kubeflow 
```

