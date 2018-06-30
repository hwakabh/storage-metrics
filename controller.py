# to manage remote docker host, use APIClient class in docker-py, not docker.from_env()
# http://docker-py.readthedocs.io/en/stable/api.html#module-docker.api.container
import docker
import json
import time
import params as param
import common_functions as common
from rabbit_monitor import Consumer
from elasticsearch import Elasticsearch


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
            print('FOR_DEBUG>>> Container seems to be not existed ...')
            return None

    # Check if image of launching container exists or not.
    def check_launch_image(self, strmark):
        img = self.client.images(name=strmark)
        if img:
            print('FOR_DEBUG>>> Image for ' + strmark + ' exist. Launching ' + strmark + ' containers...')
            return True
        else:
            print('FOR_DEBUG>>> There is no image for ' + strmark + '. ' + strmark + ' container failed to launch...')
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
            print('LOGGER>>> Specified storage does not exist.')

        print('LOGGER>>> Launching storage containers...')
        c = None
        if (strmark == 'xtremio') or (strmark == 'isilon'):
            cmd = '/usr/local/bin/python ' + strmark + '_collector.py'
            print('LOGGER>>> Try executing ' + cmd + ' on container...')
            try:
                c = self.client.create_container(image=image_name, detach=True, name=cname,
                                                 command=cmd)
                print('LOGGER>>> ' + strmark + ' container successfully created.')
            except Exception as e:
                print('LOGGER>>> Error when creating container of collector for ' + strmark + '...')
                print('Errors : ', e.args)
        else:
            pass
        return c

    def launch_container(self, strmark):
        cname = 'smetrics_' + strmark

        # Checking for avoiding name conflict
        containers = self.get_containers(isall=False)
        if cname in containers:
            print('LOGGER>>> Could not start container '
                  'because ' + strmark + ' container is already running with same name as ' + cname)
            print('LOGGER>>> Stop and Force-removing container ' + cname)
            self.kill_container(strmark=strmark, isremove=True)
        else:
            containers = self.get_containers(isall=True)
            if cname in containers:
                print('LOGGER>>> Could not start container '
                      'because ' + strmark + ' container was not removed with same name as ' + cname)
                print('LOGGER>>> Removing remaining container ' + cname)
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
        print('LOGGER>>> Creating ' + strmark + ' container and starting it ...')
        c = None
        if (strmark == 'postgres') or (strmark == 'rabbitmq') or (strmark == 'elasticsearch'):
            try:
                c = self.client.create_container(image=image_name, detach=True, name=cname,
                                                 ports=hostports, host_config=hostconfig)
                print('LOGGER>>> ' + strmark + ' container successfully created.')
            except Exception as e:
                print('LOGGER>>> Error when creating ' + strmark + ' containers...')
                print('Errors : ', e.args)
        # case if creating storage collector containers
        elif (strmark == 'xtremio') or (strmark == 'isilon'):
            c = self.launch_storage_container(strmark=strmark)
        else:
            print('FOR_DEBUG>>> Specified strmark seems to be wrong, check your parameters.')

        # Starting containers
        try:
            self.client.start(c)
            print('LOGGER>>> ' + strmark + ' container started.')
        except Exception as e:
            print('LOGGER>>> Error when starting ' + strmark + ' containers...')
            print('Errors : ', e.args)

    def kill_container(self, strmark, isremove):
        container_id = self.get_container_id(strmark)
        if isremove:
            print('>>> Removing ' + strmark + '(ID: ' + container_id + ') ...')
            self.client.remove_container(container=container_id, force=True)
        else:
            print('>>> Stopping ' + strmark + '(ID: ' + container_id + ') ...')
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
        print('LOGGER>>> Please check strmark')

    for m in metrics:
        body = get_data_from_postgres(strmark=strmark, metric=m)
        if type(body) is list:
            for b in body:
                es.index(index=strmark, doc_type=m, body=b)
        else:
            es.index(index=strmark, doc_type=m, body=body)

    print('LOGGER>>> Data sent to ElasticSearch.')
    res = es.search(index=strmark, body={"query": {"match_all": {}}})
    # print(json.dumps(res))


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
    print('LOGGER>>> Checking if ElasticSearch exists or not ...')
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
    print('LOGGER>>> Controller started by \'python controller.py\'')

    # --- Instantiate docker class
    d = None
    try:
        d = Dockerengine()
    except Exception as e:
        print('LOGGER>>> Error when instantiate docker class.')
        print('Errors : ', e.args)

    # --- start postgres
    print('LOGGER>>> Launching postgres container...')
    if d.check_launch_image(strmark='postgres'):
        d.launch_container(strmark='postgres')
    else:
        # Case if there's no image for postgres
        pass

    # --- start rabbitmq
    print('LOGGER>>> Launching RabbitMQ container...')
    if d.check_launch_image(strmark='rabbitmq'):
        d.launch_container(strmark='rabbitmq')
    else:
        # Case if there's no image for rabbitmq
        pass

    print('LOGGER>>> Waiting for waking up RabbitMQ container for 5 Seconds ....')
    time.sleep(5)

    # --- start xtremio_collector(data collected would be inserted to postgres by each collector)
    if d.check_launch_image(strmark=param.xtremio_imgname):
        print('LOGGER>>> Launching XtremIO-Collector container...')
        d.launch_container(strmark='xtremio')
    else:
        # Case if there's no image for smetric/xtremiocollector, start to build image and launch container
        pass

    # --- start isilon_collector(data collected would be inserted to postgres by each collector)
    if d.check_launch_image(strmark=param.isilon_imgname):
        print('LOGGER>>> Launching Isilon-Collector container...')
        d.launch_container(strmark='isilon')
    else:
        # Case if there's no image for smetric/isiloncollector, start to build image and launch container
        pass

    # --- wait for collectors complete(Check if 2 messages in each channel)
    is_complete = start_message_monitor()
    if is_complete:
        print('LOGGER>>> All the collector completed ...!!')

        # --- check if ElasticSearch exists
        es_state = check_es_existence()
        if es_state == 'RUNNING':
            print('LOGGER>>> ElasticSearch exist. Nothing to do in this step.')
        elif es_state == 'STOPPED':
            print('LOGGER>>> ElasticSearch exists, but stopped. Attempting to start it...')
            d.start_container(strmark='elasticsearch')
        else:
            print('LOGGER>>> No ElasticSearch exists, creating new one.')
            d.launch_container(strmark='elasticsearch')

        # --- send data from postgres to ElasticSearch
        send_data_to_es(strmark='xtremio')
        send_data_to_es(strmark='isilon')

    # -- print out containers for checking
    containers = d.get_containers(isall=True)
    print(containers)

    # --- finally kill and remove container Postgres and RabbitMQ
    # # Stop container(if isremove=True, container would be destroyed)
    # d.kill_container('clever_wing', isremove=False)
    # # Stop and remove all containers
    # for ck in containers.keys():
    #     print(ck)
    #     d.kill_container(ck, isremove=True)
    print('LOGGER>>> Cleaning up container done. Controller has done its task ...!!')


if __name__ == '__main__':
    main()
