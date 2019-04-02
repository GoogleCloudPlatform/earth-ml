FROM tensorflow/tensorflow:latest-py3

COPY requirements.txt /
RUN pip install -U -r /requirements.txt

ENV WORKDIR /app
WORKDIR ${WORKDIR}
COPY . ${WORKDIR}

ENV GOOGLE_APPLICATION_CREDENTIALS credentials.json
ENV PROJECT project-earth-2018
ENV ML_ENGINE_TOPIC ml-engine

CMD ["python", "main.py"]