import pika
import params as param


# RabbitMQ : Controller is 'Consumer' and would 'Consume(=Receive)' message
class Consumer:
    def __init__(self):
        self.rabbit_ip = param.mq_address

    def receive_message(self, strmark):
        connection = pika.BlockingConnection(pika.ConnectionParameters(host=self.rabbit_ip))

        try:
            channel = connection.channel()
            # create channel to send message
            channel.queue_declare(queue=strmark)

            print('FOR_DEBUG>>> Waiting for messages from Channel ' + strmark + '.')

            def callback(ch, method, properties, body):
                print('FOR_DEBUG>>> Received %s ' % (body, ))

            channel.basic_consume(callback, queue=strmark, no_ack=True)
            try:
                channel.start_consuming()
            except KeyboardInterrupt:
                channel.stop_consuming()
                return True
            connection.close()

            print('LOGGER>>> Finish receiving messages from Channel ' + strmark + '.')

        except Exception as e:
            print('LOGGER>>> Something wrong with RabbitMQ ...')
            print('Errors : ', e.args)


if __name__ == '__main__':
    # rabbit = Consumer()
    # rabbit.receive_message()
    print('Executed by python console...')