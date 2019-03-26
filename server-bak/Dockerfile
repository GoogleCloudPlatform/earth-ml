# The Dockerfile defines the image's environment.
# Import Python runtime and set up working directory.

# FROM python:3.6-alpine
FROM tensorflow/tensorflow:latest-py3
# FROM tensorflow/tensorflow:latest-gpu-py3
WORKDIR /app
ADD . .

# Install any necessary dependencies
RUN pip install -r requirements.txt

# Open port 8080 for serving the webpage
EXPOSE 8080

# Run app.py when the container launches
CMD ["python", "app.py"]