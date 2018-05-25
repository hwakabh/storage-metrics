# to manage remote docker host, use APIClient class in docker-py, not docker.from_env()
# http://docker-py.readthedocs.io/en/stable/api.html#module-docker.api.container
import docker
import params as param


class Common:
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
        if strmark in containers:
            return containers.get(strmark)
        else:
            print('FOR_DEBUG>>> Container seems to be not existed ...')
            return None

    def launch_container(self, strmark, cname):
        # Checking for avoiding name conflict
        running_containers = self.get_containers(isall=False)
        if cname in running_containers:
            print('LOGGER>>> Could not start container because ' + strmark + ' container is already running with same name as ' + cname)
        else:
            all_containers = self.get_containers(isall=True)
            if cname in all_containers:
                print('LOGGER>>> Could not start container because ' + strmark + ' container was not removed with same name as ' + cname)
            else:
                # case if no name conflict
                image_name = strmark + ':latest'
                print('LOGGER>>> Creating ' + strmark + ' containers and starting it ...')
                c = None
                try:
                    c = self.client.create_container(image=image_name, detach=True, name=cname)
                    print('LOGGER>>> ' + strmark + ' container successfully created.')
                except Exception as e:
                    print('LOGGER>>> Error when creating ' + strmark + 'containers...')
                    print('Errors : ', e.args)
                try:
                    self.client.start(c)
                except Exception as e:
                    print('LOGGER>>> Error when starting ' + strmark + 'containers...')
                    print('Errors : ', e.args)
                print('LOGGER>>> ' + strmark + ' container started.')

    # Delete container by name(strmark)
    def kill_container(self, strmark, isremove):
        container_id = self.get_container_id(strmark)
        if isremove:
            print('>>> Removing ' + strmark + '(ID: ' + container_id + ') ...')
            self.client.remove_container(container=container_id, force=True)
        else:
            print('>>> Stopping ' + strmark + '(ID: ' + container_id + ') ...')
            self.client.stop(container=container_id)


def main():
    # --- starting controller
    print('LOGGER>>> Controller started by \'python controller.py\'')

    # --- Instantiate docker class
    d = None
    try:
        d = Common()
    except Exception as e:
        print('LOGGER>>> Error when instantiate docker class.')
        print('Errors : ', e.args)

    # --- start postgres
    print('LOGGER>>> Starting postgres container...')
    d.launch_container(strmark='postgres',cname=param.pg_cname)

    # --- start rabbitmq
    print('LOGGER>>> Starting RabbitMQ container...')
    d.launch_container(strmark='rabbitmq',cname=param.mq_cname)

    # --- start rabbit_monitor

    # --- initialize task-status of each collector

    # --- start xtremio_collector(data collected would be inserted to postgres by each collector)

    # --- start isilon_collector(data collected would be inserted to postgres by each collector)

    # --- wait for collectors complete

    print('LOGGER>>> All the collector completed ...!!')

    # --- check if ElasticSearch exists

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