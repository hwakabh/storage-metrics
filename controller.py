# to manage remote docker host, use APIClient class in docker-py, not docker.from_env()
# http://docker-py.readthedocs.io/en/stable/api.html#module-docker.api.container
import docker
import params as param
import common_functions as common
from rabbit_monitor import Consumer
from rabbit_monitor import TaskState


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


class ElasticSearch():
    def __init__(self):
        pass

    def get_data_from_postgres(self):
        pass

    # Create queries and json objects to posting ElasticSearch
    def json_builder(self):
        pass

    # HTTP post according to flag specified
    def send_data_to_es(self):
        pass


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


# Integration method for execute all
def send_all_data(storage):
    # storage = 'xtremio', 'isilon'
    pass


def start_message_monitor():
    rabbit = Consumer()


def initialize_collector_status():
    ts = TaskState()
    print(ts.xtermioc_status)
    print(ts.isilonc_status)


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

    # # --- start rabbit_monitor
    # start_message_monitor()

    # # --- initialize task-status of each collector
    # initialize_collector_status()

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

    # --- wait for collectors complete

    print('LOGGER>>> All the collector completed ...!!')

    # --- check if ElasticSearch exists
    if check_es_existence() == 'RUNNING':
        print('LOGGER>>> ElasticSearch exist. Nothing to do in this step.')
    elif check_es_existence() == 'STOPPED':
        print('LOGGER>>> ElasticSearch exists, but stopped. Attempting to start it...')
        d.start_container(strmark='elasticsearch')
    else:
        print('LOGGER>>> No ElasticSearch exists, creating new one.')
        d.launch_container(strmark='elasticsearch')

    # --- send data from postgres to ElasticSearch

    # --- finally kill and remove container Postgres and RabbitMQ
    # # Stop container(if isremove=True, container would be destroyed)
    # d.kill_container('clever_wing', isremove=False)
    # # Stop and remove all containers
    # for ck in containers.keys():
    #     print(ck)
    #     d.kill_container(ck, isremove=True)

    containers = d.get_containers(isall=True)
    print(containers)


if __name__ == '__main__':
    main()