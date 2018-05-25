#!/bin/bash

echo "stoping all running containers"
docker stop $(docker ps -aq)
echo "removing all containers"
docker rm $(docker ps -aq)
