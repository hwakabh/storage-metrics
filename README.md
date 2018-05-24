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
- ElasticSearch
- Kibana
- Postgres
- Python
- CentOS Linux

## Usage
- Python programs runs by Linux cron jobs.(daily)