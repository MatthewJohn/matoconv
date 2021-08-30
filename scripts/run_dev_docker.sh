#!/bin/bash

rm -rf build matoconv.egg-info dist

docker build . -t matoconv-test
docker run -p8091:8091 --name=matoconv-test -d matoconv-test

docker logs -f matoconv-test &
echo 'Running on :8091. Press <Enter> to stop and destroy'
read

docker kill matoconv-test
docker rm matoconv-test
