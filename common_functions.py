# common functions for each collector
import pika
import params as param


# RabbitMQ : each collector is 'Producer' and would 'publish(=Send)' message
def send_message(msg):
    connection = pika.BlockingConnection(pika.ConnectionParameters(host=param.mq_address))
    return_value = False
    try:
        channel = connection.channel()
        # create channel to send message
        channel.queue_declare(queue=param.mq_quename)
        print('FOR_DEBUG>>> Create channel ' + param.mq_quename + ' with RabbitMQ...')
        channel.basic_publish(exchange='', routing_key=param.mq_quename, body=msg)
        print('FOR_DEBUG>>> [x]Messaage \'' + msg + '\' successfully sent to ' + param.mq_quename)
        return_value = True
    except Exception as e:
        print('LOGGER>>> Error when sending message ...')
        print('Errors : ', e.args)
    finally:
        try:
            connection.close()
        except Exception as e:
            print('LOGGER>>> Error when sending message ...')
            print('Errors : ', e.args)
    return return_value


def get_http_response():
    pass


def get_postgres_connection():
    pass


def run_sql_query():
    pass


def create_table():
    pass


def send_data_to_postgres():
    pass


def main():
    send_message('postgres_Start')
    send_message('rabbit_Start')
    send_message('xtremio_Start')
    send_message('isilon_Start')


if __name__ == '__main__':
    main()