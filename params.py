# Configuration parameters for each components

# For Remote Docker engine
docker_ip = '10.62.130.167'
docker_port = 2375
docker_api_version = '1.37'

max_running = 3
timeout = 100000


# -- For Postgres
pg_address = '10.62.130.167'
pg_ports = [5432,]
# pg_portmap = {5432: 32768}
pg_portmap = {5432: 5432}
pg_username = 'postgres'
pg_password = 'postgres'
pg_database = 'postgres'

# -- For RabbitMQ
mq_address = '10.62.130.167'
mq_ports = [25672, 5672, 5671, 4369, 15672]
# mq_portmap = {25672: 32776, 5672: 32777, 5671: 32778, 4369: 32779}
mq_portmap = {25672: 25672, 5672: 5672, 5671: 5671, 4369: 4369, 15672: 15672}
mq_quename = 'smetric_queue'

# -- For ElasticSearch
es_address = '10.62.130.167'
es_ports = [9200,]
es_portmap = {9200: 9200}
index = {
    'xtremio': 'xtremio',
    'isilon': 'isilon'
}

# -- For XtremIO
xtremio_address = '10.32.210.156'
xtremio_user = 'admin'
xtremio_pass = 'Xtrem10'
xtremio_imgname = 'smetrics/xtremiocollector'
xtremio_clogpath = '/var/log/collector/xtremio'
xtremio_hlogpath = '/home/smetric/log/xtremio'

# -- For Isilon
isilon_address = '10.32.239.181'
isilon_user = 'root'
isilon_pass = 'nasadmin'
isilon_imgname = 'smetrics/isiloncollector'
isilon_clogpath = '/var/log/collector/isilon'
isilon_hlogpath = '/home/smetric/log/isilon'
