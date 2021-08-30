#!/bin/bash

docker build . -t matoconv-test
cont=$(docker run -p8091:8091 -d matoconv-test)

echo 'Running on :8091. Press <Enter> to stop and destroy'
read

docker kill $cont
docker rm $cont
