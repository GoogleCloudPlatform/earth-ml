#!/bin/bash

# Deploying the web application.
( cd webapp ; ng build --prod )
gcloud app deploy webapp
