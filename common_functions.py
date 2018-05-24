import docker


def main():
    # to manage remote docker host, use APIClient class in docker-py, not docker.from_env()
    # http://docker-py.readthedocs.io/en/stable/api.html#module-docker.api.container
    client = docker.APIClient(base_url='tcp://10.0.10.100:2375', tls=False, version='1.37')
    images = client.images()
    container_list = client.containers()
    print('Before : ' +str(len(container_list)))

    print('==== Creating postgres container....')
    c = client.create_container(image='postgres:latest', detach=True)
    print('==== Starting postgres container....')
    client.start(c)
    container_list = client.containers()
    print('After : ' +str(len(container_list)))

    # show running containers
    container_ids = []
    print('==== Listing up containers running on Remote Docker Engine...')
    for i in range(len(container_list)):
        print('ContainerID : ' + str(container_list[i]['Id']) + ' ||| ContainerName : ' + str(container_list[i]['Names']))
        container_ids.append(str(container_list[i]['Id']))

    # Stop all containers
    print('==== Stopping containers running on Remote Docker Engine...')
    for container_id in container_ids:
        client.stop(container=container_id)
    container_list = client.containers()
    print('After : ' +str(len(container_list)))

    # Remove all containers(Force stopped)
    container_list = client.containers(all=True)
    print('==== Removing containers running on Remote Docker Engine...')
    container_ids = []
    for i in range(len(container_list)):
        print('ContainerID : ' + str(container_list[i]['Id']) + ' ||| ContainerName : ' + str(container_list[i]['Names']))
        container_ids.append(str(container_list[i]['Id']))
    for container_id in container_ids:
        client.remove_container(container=container_id, force=True)


if __name__ == '__main__':
    main()