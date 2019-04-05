#This container contains your model and any helper scripts specific to your model.
FROM tensorflow/tensorflow:1.12.0-py3

ADD ./service.py /opt/service.py
ADD ./project-earth-2018-sa.json  /opt/project-earth-2018-sa.json
RUN chmod +x /opt/service.py
ENV GOOGLE_APPLICATION_CREDENTIALS /opt/project-earth-2018-sa.json

# Downloading gcloud package
RUN curl https://dl.google.com/dl/cloudsdk/release/google-cloud-sdk.tar.gz > /tmp/google-cloud-sdk.tar.gz

# Installing the package
RUN mkdir -p /usr/local/gcloud \
  && tar -C /usr/local/gcloud -xvf /tmp/google-cloud-sdk.tar.gz \
  && /usr/local/gcloud/google-cloud-sdk/install.sh

# Adding the package path to local
ENV PATH $PATH:/usr/local/gcloud/google-cloud-sdk/bin

RUN gcloud config set project project-earth-2018
RUN gcloud auth activate-service-account project-earth@project-earth-2018.iam.gserviceaccount.com --key-file=$GOOGLE_APPLICATION_CREDENTIALS --project=project-earth-2018
RUN gcloud container clusters get-credentials projectearth2018 --zone us-central1-a --project project-earth-2018
RUN gcloud config list

# Set the Kubernetes version as found in the UCP Dashboard or API
ENV k8sversion v1.13.1

# Get the kubectl binary.
RUN curl -LO https://storage.googleapis.com/kubernetes-release/release/$k8sversion/bin/linux/amd64/kubectl

# Make the kubectl binary executable.
RUN chmod +x ./kubectl

# Move the kubectl executable to /usr/local/bin.
RUN mv ./kubectl /usr/local/bin/kubectl

RUN pip install flask pyyaml

EXPOSE 5000

ENTRYPOINT ["/usr/bin/python", "/opt/service.py"]