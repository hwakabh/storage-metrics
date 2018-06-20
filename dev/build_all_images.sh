#!/bin/bash

cd /root/storage-metrics/

echo ">>>>>>>>> Building Collector container image..."
docker build -t smetrics/controller:latest -f ./dockersrc/Dockerfile_controller .

echo ""
echo ""
echo ">>>>>>>>> Building XtremIO container image..."
docker build -t smetrics/xtremiocollector:latest -f ./dockersrc/Dockerfile_xtremio .

echo ""
echo ""
echo ">>>>>>>>> Building Isilon container image..."
docker build -t smetrics/isiloncollector:latest -f ./dockersrc/Dockerfile_isilon .

echo ""
echo ""
echo ">>>>>>>>> Built all images for storage-collectors !!"
