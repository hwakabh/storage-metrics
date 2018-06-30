import pika
import logging
import params as param

logger = logging.getLogger(__name__)


# RabbitMQ : Controller is 'Consumer' and would 'Consume(=Receive)' message
class Consumer:
    def __init__(self):
        self.rabbit_ip = param.mq_address

    def receive_message(self, strmark):
        connection = pika.BlockingConnection(pika.ConnectionParameters(host=self.rabbit_ip))

        try:
            channel = connection.channel()
            # create channel to send message
            queue_state = channel.queue_declare(queue=strmark, durable=True, passive=True)
            queue_empty = queue_state.method.message_count == 0

            logger.info('FOR_DEBUG>>> Waiting for messages from Channel ' + strmark + '.')

            def callback(ch, method, properties, body):
                logger.info('FOR_DEBUG>>> Received %s ' % (body, ))

            while queue_empty:
                method, properties, body = channel.basic_get(queue=strmark, no_ack=True)
                callback(channel, method, properties, body)

            logger.info('FOR_DEBUG>>> Finish receiving messages from Channel ' + strmark + '.')
            connection.close()
            return True

        except Exception as e:
            logger.error('FOR_DEBUG>>> Something wrong with RabbitMQ ...')
            logger.error('Errors : ', e.args)

