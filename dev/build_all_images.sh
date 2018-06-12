#!/bin/bash

cd /root/storage-metrics/

echo "Building XtremIO container image..."
docker build -t smetrics/xtremiocollector:latest -f ./dockersrc/Dockerfile_xtremio .

echo "Building Isilon container image..."
docker build -t smetrics/isiloncollector:latest -f ./dockersrc/Dockerfile_isilon .

echo "Built all images for storage-collectors"
