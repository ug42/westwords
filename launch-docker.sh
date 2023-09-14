#!/bin/bash
DOCKER_BIN="/usr/bin/docker"

$DOCKER_BIN run \
  --log-driver=local \
  --log-opt max-size=50m \
  -l debug \
  --log-opt max-file=6 \
  --name=westwords \
  -p 8000:8000 \
  -d westwords:latest
