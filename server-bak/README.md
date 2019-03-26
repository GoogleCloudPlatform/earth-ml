1. [Install the Google Cloud SDK](https://cloud.google.com/sdk/docs/quickstarts), which includes the gcloud command-line tool.

1. After installing Cloud SDK, install the kubectl command-line tool by running the following command:
```sh
gcloud components install kubectl
```

1. Configure Docker to use the gcloud command-line tool to authenticate requests to Container Registry.
```sh
# You are only required to do this once.
gcloud auth configure-docker
```

1. Set your default [`project`](https://support.google.com/cloud/answer/6158840) and [`compute zone`](https://cloud.google.com/compute/docs/regions-zones/regions-zones#available). If you want to use GPUs, make sure to use a [zone that supports GPUs](https://cloud.google.com/compute/docs/gpus/).
```sh
PROJECT_ID=your-project-id

gcloud config set project $PROJECT_ID
gcloud config set compute/zone us-central1-c
```