# Use the official lightweight Python image.
# https://hub.docker.com/_/python
FROM python:3.12-slim

# Allow statements and log messages to immediately appear in the Knative logs
ENV PYTHONUNBUFFERED True

# Copy local code to the container image.
ENV APP_HOME /app
WORKDIR $APP_HOME
COPY . /app

# Install production dependencies.
RUN pip install --no-cache-dir -r requirements.txt

# Run as non-root
RUN adduser --system --group --no-create-home app
RUN chown -R app:app /app 
USER app

EXPOSE 8000/tcp
EXPOSE 80/tcp
EXPOSE 443/tcp

# Run the web service on container startup. Here we use the gunicorn
# webserver, with one worker process and 8 threads.
# For environments with multiple CPU cores, increase the number of workers
# to be equal to the cores available.
# Timeout is set to 0 to disable the timeouts of the workers to allow Cloud Run to handle instance scaling.
CMD exec gunicorn --bind :${PORT-80} --workers 1 --worker-class eventlet --threads 8 --timeout 0 server:app
