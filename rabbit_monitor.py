import pika
import params as param


# RabbitMQ : Controller is 'Consumer' and would 'Consume(=Receive)' message
class Consumer:
    def __init__(self):
        self.rabbit_ip = param.mq_address

    def receive_message(self):
        connection = pika.BlockingConnection(pika.ConnectionParameters(host=self.rabbit_ip))
        channel = connection.channel()

        # TODO: Error-handle if failed declare
        channel.queue_declare(queue=param.mq_quename)

        print('[*] Waiting for messages. To exit, press \'Control+C\'')

        def callback(ch, method, properties, body):
            print('[x] Received %r' % (body,))

        channel.basic_consume(callback, queue=param.mq_quename, no_ack=True)
        channel.start_consuming()


def main():
    rabbit = Consumer()
    rabbit.receive_message()


if __name__ == '__main__':
    main()