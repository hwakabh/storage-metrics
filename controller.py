# to manage remote docker host, use APIClient class in docker-py, not docker.from_env()
# http://docker-py.readthedocs.io/en/stable/api.html#module-docker.api.container
import docker
import time
import datetime
import logging

import params as param
import common_functions as common
from rabbit_monitor import Consumer
from elasticsearch import Elasticsearch

logfilename = "./logs/" + datetime.datetime.now().strftime("%Y%m%d_controller") + ".log"
# logging.basicConfig()
_detail_formatting = "%(asctime)s : %(name)s - %(levelname)s : %(message)s"
logging.basicConfig(level=logging.DEBUG, format=_detail_formatting, filename=logfilename,)
logging.getLogger("modules").setLevel(level=logging.DEBUG)
console = logging.StreamHandler()
console_formatter = logging.Formatter("%(asctime)s : %(message)s")
console.setFormatter(console_formatter)
console.setLevel(logging.INFO)
logging.getLogger("modules").addHandler(console)

logger = logging.getLogger(__name__)
logging.getLogger(__name__).addHandler(console)


class Dockerengine:
    def __init__(self):
        self.docker_ip = param.docker_ip
        self.docker_port = param.docker_port
        self.docker_api_version = param.docker_api_version
        self.target = 'tcp://' + self.docker_ip + ':' + str(self.docker_port)
        self.client = docker.APIClient(base_url=self.target, tls=False, version=self.docker_api_version)

    def get_containers(self, isall):
        if isall:
            container_list = self.client.containers(all=True)
        else:
            container_list = self.client.containers()

        container_ids = {}
        for i in range(len(container_list)):
            container_ids[str(container_list[i]['Names'][0]).replace('/','')] = str(container_list[i]['Id'])
        # for k, v in container_ids.items():
        #     print('ContainerName : ' + k + '\t ID : ' + v)
        return container_ids

    def get_container_id(self, strmark):
        containers = self.get_containers(isall=True)
        cname = 'smetrics_' + strmark
        if cname in containers:
            return containers.get(cname)
        else:
            logger.warning('FOR_DEBUG>>> Container seems to be not existed ...')
            return None

    # Check if image of launching container exists or not.
    def check_launch_image(self, strmark):
        img = self.client.images(name=strmark)
        if img:
            logger.info('FOR_DEBUG>>> Image for ' + strmark + ' exist. Launching ' + strmark + ' containers...')
            return True
        else:
            logger.info('FOR_DEBUG>>> There is no image for ' + strmark + '. ' + strmark + ' container failed to launch...')
            return False

    def start_container(self, strmark):
        pass

    def launch_storage_container(self, strmark):
        image_name = ''
        cname = 'smetrics_' + strmark

        if strmark == 'xtremio':
            image_name = param.xtremio_imgname + ':latest'
        elif strmark == 'isilon':
            image_name = param.isilon_imgname + ':latest'
        else:
            logger.error('FOR_DEBUG>>> Specified storage does not exist.')

        logger.info('FOR_DEBUG>>> Launching storage containers...')
        c = None
        if (strmark == 'xtremio') or (strmark == 'isilon'):
            cmd = '/usr/local/bin/python ' + strmark + '_collector.py'
            logger.info('FOR_DEBUG>>> Try executing ' + cmd + ' on container...')
            try:
                c = self.client.create_container(image=image_name, detach=True, name=cname,
                                                 command=cmd)
                logger.info('FOR_DEBUG>>> ' + strmark + ' container successfully created.')
            except Exception as e:
                logger.error('FOR_DEBUG>>> Error when creating container of collector for ' + strmark + '...')
                logger.error('Errors : ', e.args)
        else:
            pass
        return c

    def launch_container(self, strmark):
        cname = 'smetrics_' + strmark

        # Checking for avoiding name conflict
        containers = self.get_containers(isall=False)
        if cname in containers:
            logger.info('FOR_DEBUG>>> Could not start container '
                  'because ' + strmark + ' container is already running with same name as ' + cname)
            logger.info('FOR_DEBUG>>> Stop and Force-removing container ' + cname)
            self.kill_container(strmark=strmark, isremove=True)
        else:
            containers = self.get_containers(isall=True)
            if cname in containers:
                logger.info('FOR_DEBUG>>> Could not start container '
                      'because ' + strmark + ' container was not removed with same name as ' + cname)
                logger.info('FOR_DEBUG>>> Removing remaining container ' + cname)
                self.kill_container(strmark=strmark, isremove=True)

        # Set parameters for launching container(case if no name conflict)
        hostports = ''
        hostconfig = ''
        image_name = ''

        if strmark == 'postgres':
            image_name = strmark + ':latest'
            hostports = param.pg_ports
            hostconfig = self.client.create_host_config(port_bindings=param.pg_portmap)
        elif strmark == 'rabbitmq':
            image_name = strmark + ':latest'
            hostports = param.mq_ports
            hostconfig = self.client.create_host_config(port_bindings=param.mq_portmap)
        elif strmark == 'elasticsearch':
            image_name = strmark + ':latest'
            hostports = param.es_ports
            hostconfig = self.client.create_host_config(port_bindings=param.es_portmap)
        else:
            pass

        # Start launching container(case if creating common containers)
        logger.info('FOR_DEBUG>>> Creating ' + strmark + ' container and starting it ...')
        c = None
        if (strmark == 'postgres') or (strmark == 'rabbitmq') or (strmark == 'elasticsearch'):
            try:
                c = self.client.create_container(image=image_name, detach=True, name=cname,
                                                 ports=hostports, host_config=hostconfig)
                logger.info('FOR_DEBUG>>> ' + strmark + ' container successfully created.')
            except Exception as e:
                logger.error('LOGGER>>> Error when creating ' + strmark + ' containers...')
                logger.error('Errors : ', e.args)
        # case if creating storage collector containers
        elif (strmark == 'xtremio') or (strmark == 'isilon'):
            c = self.launch_storage_container(strmark=strmark)
        else:
            logger.error('FOR_DEBUG>>> Specified strmark seems to be wrong, check your parameters.')

        # Starting containers
        try:
            self.client.start(c)
            logger.info('FOR_DEBUG>>> ' + strmark + ' container started.')
        except Exception as e:
            logger.error('FOR_DEBUG>>> Error when starting ' + strmark + ' containers...')
            logger.error('Errors : ', e.args)

    def kill_container(self, strmark, isremove):
        container_id = self.get_container_id(strmark)
        if (strmark == 'kibana') or (strmark == 'elasticsearch'):
            pass
        else:
            if isremove:
                logger.info('>>> Removing ' + strmark + '(ID: ' + container_id + ') ...')
                self.client.remove_container(container=container_id, force=True)
            else:
                logger.info('>>> Stopping ' + strmark + '(ID: ' + container_id + ') ...')
                self.client.stop(container=container_id)


def send_data_to_es(strmark):
    # Instantiate ElasticSearch Class
    es_url = 'http://' + param.es_address + ':' + str(param.es_ports[0])
    es = Elasticsearch(es_url)

    metrics = []
    if strmark == 'xtremio':
        metrics = ['capacity', 'cl_performance', 'sc_performance']
    elif strmark == 'isilon':
        metrics = ['capacity', 'quota', 'cpu', 'bandwidth']
    else:
        logger.error('FOR_DEBUG>>> Please check strmark')

    for m in metrics:
        body = get_data_from_postgres(strmark=strmark, metric=m)
        if type(body) is list:
            for b in body:
                es.index(index=strmark, doc_type=m, body=b)
        else:
            es.index(index=strmark, doc_type=m, body=body)

    logger.info('FOR_DEBUG>>> Data collected by ' + strmark + '_collector sent to ElasticSearch.')
    res = es.search(index=strmark, body={"query": {"match_all": {}}})


def get_data_from_postgres(strmark, metric):
    table_name = strmark + '_' + metric + '_table'
    pg = common.Postgres(hostname=param.pg_address, port=param.pg_ports[0],
                         username=param.pg_username, password=param.pg_password, database=param.pg_database)
    pg.connect()
    cur = pg.get_connection().cursor()
    q = 'SELECT * FROM ' + table_name
    cur.execute(q)
    ret = cur.fetchall()
    table_header = [desc[0] for desc in cur.description]

    # Convert query result to Json for posting ElasticSearch
    json_ret = parse_to_json(header=table_header, data=ret)

    return json_ret


# Create queries and json objects to posting ElasticSearch
def parse_to_json(header, data):
    json_data = {}
    if len(data) == 1:
        for i in range(len(header)):
            json_data[str(header[i])] = data[0][i]
        return json_data
    else:
        return_array = []
        for d in range(len(data)):
            for i, h in enumerate(header):
                json_data[h] = data[d][i]
            return_array.append(json_data)
        return return_array

# def build_image():
#     print('DEBUG>>> Building up docker images...')
#     f = open('./dockersrc/Dockerfile_Isilon', 'rb')
#     d2 = Dockerengine()
#     response = [line for line in d2.client.build(fileobj=f, tag='smetrics/isiloncollector')]
#     for r in response:
#         print(r)
#


def check_es_existence():
    d = Dockerengine()
    es_cname = 'smetrics_elasticsearch'
    logger.info('FOR_DEBUG>>> Checking if ElasticSearch exists or not ...')
    running_containers = d.get_containers(isall=False)
    all_containers = d.get_containers(isall=True)

    # Elasticsearch states: RUNNING, STOPPED, NONE
    if es_cname in running_containers:
        return 'RUNNING'
    else:
        if es_cname in all_containers:
            return 'STOPPED'
        else:
            return 'NONE'


# To consume all messages
def start_message_monitor():
    rabbit = Consumer()
    is_complete_xtremio = rabbit.receive_message(strmark='xtremio')
    is_complete_isilon = rabbit.receive_message(strmark='isilon')

    if is_complete_xtremio and is_complete_isilon:
        return True
    else:
        return False


def main():
    # --- starting controller
    logger.info('FOR_DEBUG>>> Controller started by \'python controller.py\'')

    # --- Instantiate docker class
    d = None
    try:
        d = Dockerengine()
    except Exception as e:
        logger.error('FOR_DEBUG>>> Error when instantiate docker class.')
        logger.error('Errors : ', e.args)

    # --- start postgres
    logger.info('FOR_DEBUG>>> Launching postgres container...')
    if d.check_launch_image(strmark='postgres'):
        d.launch_container(strmark='postgres')
    else:
        # Case if there's no image for postgres
        pass

    # --- start rabbitmq
    logger.info('FOR_DEBUG>>> Launching RabbitMQ container...')
    if d.check_launch_image(strmark='rabbitmq'):
        d.launch_container(strmark='rabbitmq')
    else:
        # Case if there's no image for rabbitmq
        pass

    logger.info('FOR_DEBUG>>> Waiting for waking up RabbitMQ container for 5 Seconds ....')
    time.sleep(5)

    # --- start xtremio_collector(data collected would be inserted to postgres by each collector)
    if d.check_launch_image(strmark=param.xtremio_imgname):
        logger.info('FOR_DEBUG>>> Launching XtremIO-Collector container...')
        d.launch_container(strmark='xtremio')
    else:
        # Case if there's no image for smetric/xtremiocollector, start to build image and launch container
        pass

    # --- start isilon_collector(data collected would be inserted to postgres by each collector)
    if d.check_launch_image(strmark=param.isilon_imgname):
        logger.info('FOR_DEBUG>>> Launching Isilon-Collector container...')
        d.launch_container(strmark='isilon')
    else:
        # Case if there's no image for smetric/isiloncollector, start to build image and launch container
        pass

    # --- wait for collectors complete(Check if 2 messages in each channel)
    logger.info('FOR_DEBUG>>> Message monitor started. Wait for startup consuming process for 5 seconds...')
    time.sleep(5)

    is_complete = False
    rc = 0

    while not is_complete:
        rc += 1
        try:
            is_complete = start_message_monitor()
        except Exception:
            logger.info('FOR_DEBUG>>> Some error occured when consuming messages, attempt to retry...')
            time.sleep(2)
        finally:
            if rc >= param.mq_rc:
                logger.error('FOR_DEBUG>>> Controller.py retried 10 times to consume message, aborted.')
                break
            else:
                pass

    if is_complete:
        logger.info('FOR_DEBUG>>> All the collector completed ...!!')

        # --- check if ElasticSearch exists
        logger.info('FOR_DEBUG>>> Prechecking for inserting data to ElasticSearch container...')
        es_state = check_es_existence()
        if es_state == 'RUNNING':
            logger.info('FOR_DEBUG>>> ElasticSearch exist. Nothing to do in this step.')
        elif es_state == 'STOPPED':
            logger.info('FOR_DEBUG>>> ElasticSearch exists, but stopped. Attempting to start it...')
            d.start_container(strmark='elasticsearch')
        else:
            logger.info('FOR_DEBUG>>> No ElasticSearch exists, creating new one.')
            d.launch_container(strmark='elasticsearch')

        # --- send data from postgres to ElasticSearch
        send_data_to_es(strmark='xtremio')
        time.sleep(5)
        send_data_to_es(strmark='isilon')
        time.sleep(5)

        # -- finally cleaning up containers
        containers = d.get_containers(isall=True)
        for k, v in containers.items():
            if ('kibana' in k) or ('elasticsearch' in k):
                pass
            else:
                logger.info('FOR_DEBUG>>> Container name: ' + k + ' / Container ID: ' + v)
                d.kill_container(k.replace('smetrics_',''), isremove=True)
        logger.info('FOR_DEBUG>>> Cleaning up container done. Controller has done its task ...!!')

    else:
        logger.error('FOR_DEBUG>>> Controller.py ended with some erroneous tasks...')


if __name__ == '__main__':
    main()
