FROM tensorflow/tensorflow:1.12.0-py3

ADD ./single_predict.py /opt/single_predict.py
ADD ./project-earth-2018-sa.json  /opt/project-earth-2018-sa.json
RUN chmod +x /opt/single_predict.py

ENTRYPOINT ["/usr/bin/python", "/opt/single_predict.py"]