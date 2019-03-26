# Rest API

The Rest API server is requires at least Python 3.6.

## Virtualenv

It is recommended to run the application using a virtual environment.
```sh
# Create a Python 3 virtual environment.
python3 -m virtualenv env

# Activate the virtual environment.
source env/bin/activate
```

Once you are done running, you can deactivate the virtualenv by running:
```sh
deactivate
```

## Training the model locally

```sh
python train-model.py
```

Press `Ctrl+C` or `Ctrl+\` to quit.

## Running locally

```sh
python rest-server.py
```

Press `Ctrl+C` or `Ctrl+\` to quit.

## Deploying to App Engine

```sh
gcloud app deploy
```
