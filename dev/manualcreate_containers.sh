#!/bin/bash

echo "Create postgres container..."
docker run -d --name smetric_postgres -p 5432:5432 postgres:latest
echo "Create rabbitmq container..."
docker run -d --name smetric_rabbitmq -p 25672:25672 -p 5672:5672 -p 5671:5671 -p 4369:4369 -p 15672:15672 rabbitmq:latest
