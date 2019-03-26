# Blocks Pipeline

```sh
PROJECT=your-google-cloud-project-id
BUCKET=your-cloud-storage-bucket
```

## Creating the PubSub topic and subscription

```sh
gcloud pubsub topics create regions
gcloud pubsub subscriptions create --topic regions regions
```

## Running locally

```sh
python main.py --project $PROJECT --bucket $BUCKET
```

## Running in Dataflow

```sh
python main.py --project $PROJECT --bucket $BUCKET --runner Dataflow
```