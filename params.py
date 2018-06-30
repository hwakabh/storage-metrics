# Configuration parameters for each components

# For Remote Docker engine
docker_ip = '<YOUR_DOCKER_IP>'
docker_port = 2375
docker_api_version = '<YOUR_DOCKER_VERSION>'

# -- For Postgres
pg_address = '<YOUR_POSTGRES_IP>'
pg_ports = [5432,]
# pg_portmap = {5432: 32768}
pg_portmap = {5432: 5432}
pg_username = '<YOUR_POSTGRES_USERNAME>'
pg_password = '<YOUR_POSTGRES_PASSWORD>'
pg_database = '<YOUR_POSTGRES_DATABASE>'

# -- For RabbitMQ
mq_address = 'YOUR_RABBITMQ_IP'
mq_ports = [25672, 5672, 5671, 4369, 15672]
# mq_portmap = {25672: 32776, 5672: 32777, 5671: 32778, 4369: 32779}
mq_portmap = {25672: 25672, 5672: 5672, 5671: 5671, 4369: 4369, 15672: 15672}
# Retry count for consuming RabbitMQ
mq_rc = 15

# -- For ElasticSearch
es_address = '<YOUR_ELASTICSEARCH_IP>'
es_ports = [9200,]
es_portmap = {9200: 9200}

# -- For XtremIO
xtremio_address = '<YOUR_XTREMIO_IP>'
xtremio_user = '<YOUR_XTREMIO_USERNAME>'
xtremio_pass = '<YOUR_XTREMIO_PASSWORD>'
xtremio_imgname = 'smetrics/xtremiocollector'

# -- For Isilon
isilon_address = '<YOUR_ISILON_IP>'
isilon_user = '<YOUR_ISILON_USERNAME>'
isilon_pass = '<YOUR_ISILON_PASSWORD>'
isilon_imgname = 'smetrics/isiloncollector'
