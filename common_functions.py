# common functions for each collector
import pika
import params as param


# RabbitMQ : each collector is 'Producer' and would 'publish(=Send)' message
def send_message(msg):
    connection = pika.BlockingConnection(pika.ConnectionParameters(host=param.mq_address))
    channel = connection.channel()

    # create channel to send message
    # TODO: Error-handle if failed declare
    channel.queue_declare(queue=param.mq_quename)
    print('FOR_DEBUG>>> Create channel ' + param.mq_quename + ' with RabbitMQ...')

    channel.basic_publish(exchange='', routing_key=param.mq_quename, body=msg)
    print('[x] Sent \'' + msg + '\'')


def main():
    send_message('postgres_Start')
    send_message('rabbit_Start')
    send_message('xtremio_Start')
    send_message('isilon_Start')


if __name__ == '__main__':
    main()