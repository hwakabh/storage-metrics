import common_functions as common
import params as param


def main():

    # --- Instantiate docker class
    d = None
    try:
        d = common.Common()
    except Exception as e:
        print('LOGGER>>> Error when instantiate docker class.')
        print('Errors : ', e.args)

    # --- start postgres
    try:
        print('LOGGER>>> Starting postgres container...')
        d.launch_container(strmark='postgres',cname=param.pg_cname)
        print('LOGGER>>> Postgres container started.')
    except Exception as e:
        print('LOGGER>>> Error when starting postgres container.')
        print('Errors : ', e.args)

    # --- start rabbitmq
    try:
        print('LOGGER>>> Starting RabbitMQ container...')
        d.launch_container(strmark='rabbitmq',cname=param.mq_cname)
        print('LOGGER>>> RabbitMQ container started.')
    except Exception as e:
        print('LOGGER>>> Error when starting RabbitMQ container.')
        print('Errors : ', e.args)

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