# Project Earth

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

## Setup

To set up the project in Google Cloud, you will have to set the following environment variables.
Note that the Cloud Storage bucket will be created on the setup script.
```sh
export BUCKET=your-cloud-storage-bucket
export EE_PROJECT=users/your-ee-user   # or projects/your-ee-project
```

Then run the [setup.sh](setup.sh) script to configure your project with the required resources.
Please refer to that file for further details on what it's doing.
```sh
bash setup.sh
```

## Deploying the project

Once all the resources are set, please run the [deploy.sh](deploy.sh) script to deploy all the required services.
```sh
bash deploy.sh
```