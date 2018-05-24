# to manage remote docker host, use APIClient class in docker-py, not docker.from_env()
# http://docker-py.readthedocs.io/en/stable/api.html#module-docker.api.container
import docker


class Common:
    def __init__(self):
        # Loading config.json file and set them to class properties
        # Error handle if config.json not existed
        self.docker_host = '10.0.10.100'
        self.docker_port = 2375
        self.docker_api_version = '1.37'
        self.target = 'tcp://' + self.docker_host + ':' + str(self.docker_port)
        self.client = docker.APIClient(base_url=self.target, tls=False, version=self.docker_api_version)

    def get_containers(self, isall):
        if isall:
            container_list = self.client.containers(all=True)
            msg = 'FOR_DEBUG>>> Listing up ALL containers on Remote Docker Engine...'
        else:
            container_list = self.client.containers()
            msg = 'FOR_DEBUG>>> Listing up containers RUNNING on Remote Docker Engine...'

        print(msg)
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

    def create_container(self, strmark):
        image_name = strmark + ':latest'
        print('>>> Creating ' + strmark + ' containers and starting it ...')
        # Currently container name is generated randomly
        c = self.client.create_container(image=image_name, detach=True)
        self.client.start(c)

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
    pass

if __name__ == '__main__':
    main()