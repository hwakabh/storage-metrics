# Storage Metrics with Docker container.

## Overviews
- Collect Storage metrics(e.g. Capacity, Configurations, Performances...etc)
  - load targets from configuration files
  - Collect metrics with REST-API
- Parse collected data with Python and put into postgres container
- Load data from postgres to ElasticSearch
- Visualize ElasticSearch data with Kibana

## Components
- Docker
- Storages(Including Emulator)
  - DellEMC Isilon
  - DellEMC XtremIO

## Containers
- Kibana
- ElasticSearch
- Postgres
- RabbitMQ
- Python

## Usage
- Import required packages with pip
  - `pip install -r requirements.txt`
- Set your environmental parameters in `params.py`
- Run main function for collecting metrics.
  - `python controller.py`
  - Note that you can use `--local` option with `controller.py` if needed to print out the stdout on your machine.
- Also, you can execute each collector's script
  - Note that if the case you run them separately, confirm that postgres and rabbitmq is running on Docker engines.
  - To run postgres and rabbitmq for preparation, use `dev/manualcreate_containers.sh`