#!/bin/bash
DOCKER_BIN="/usr/bin/docker"
set -x

$DOCKER_BIN run \
  --log-driver=local \
  --log-opt max-size=50m \
  -l debug \
  --log-opt max-file=6 \
  --name=westwords \
  -p 80:80 \
  -d westwords:${1:-latest}
