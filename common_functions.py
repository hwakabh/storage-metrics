import docker


def main():
    # to manage remote docker host, use APIClient class in docker-py, not docker.from_env()
    # http://docker-py.readthedocs.io/en/stable/api.html#module-docker.api.container
    client = docker.APIClient(base_url='tcp://10.62.130.166:2375', tls=False, version='1.37')
    images = client.images()
    container_list = client.containers()
    print('Before : ' +str(len(container_list)))

    print('==== Creating postgres container....')
    c1 = client.create_container(image='postgres:latest', detach=True, name='docker_py_test_pg')
    print('==== Starting postgres container....')
    client.start(c1)
    container_list = client.containers()
    print('After : ' +str(len(container_list)))


if __name__ == '__main__':
    main()