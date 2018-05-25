# Configuration parameters for each components
# TODO: Add port-mapping for docker-engine

# -- For XtremIO
xtremio_user = 'admin'
xtermio_pass = 'Xtrem10'
xtremio_imgname = 'smetric/xtremiocollector'
xtermio_clogpath = '/var/log/collector/xtremio'
xtermio_hlogpath = '/home/smetric/log/xtremio'
# -- For Isilon
isilon_user = 'root'
isilon_pass = 'a'
isilon_imgname = 'smetric/isiloncollector'
isilon_clogpath = '/var/log/collector/isilon'
isilon_hlogpath = '/home/smetric/log/isilon'
# -- For ElasticSearch
es_address = '10.62.130.166'
es_port = 9200
index = {
    'xtremio':'xtremio',
    'isilon':'isilon'
}
# -- For Postgres
pg_address = '10.62.130.166'
pg_port = 5432  # pg_port = {'5432':32768}
pg_srcimg = 'postgres:latest'
pg_cname = 'smetric_postgres'
# -- For RabbitMQ
mq_address = '10.62.130.166'
mq_ports = [25672, 5672, 5671, 4369]     # mq_ports = {'25672':32776, '5672':32777, '5671':32778, '4369':32779}
mq_srcimg = 'rabbitmq:latest'
mq_channel = 'smetric_queue'

# For Docker engine
max_running = 3
timeout = 100000