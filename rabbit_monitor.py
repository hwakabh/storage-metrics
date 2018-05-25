import pika
import time
import params as param


# RabbitMQ : Controller is 'Consumer' and would 'Consume(=Receive)' message
class Consumer:
    def __init__(self):
        self.rabbit_ip = param.mq_address

    def receive_message(self):
        connection = pika.BlockingConnection(pika.ConnectionParameters(host=self.rabbit_ip))

        try:
            channel = connection.channel()
            # create channel to send message
            channel.queue_declare(queue=param.mq_quename)

            print('[*] Waiting for messages. To exit, press \'Control+C\'')

            def callback(ch, method, properties, body):
                print('FOR_DEBUG>>> [x] Received %s' % (body, ))

            channel.basic_consume(callback, queue=param.mq_quename, no_ack=True)
            channel.start_consuming()

        except Exception as e:
            print('LOGGER>>> Something wrong with RabbitMQ ...')
            print('Errors : ', e.args)


def main():
    rabbit = Consumer()
    rabbit.receive_message()


if __name__ == '__main__':
    main()