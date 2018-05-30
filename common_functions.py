# common functions for each collector
import pika
import requests
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


def get_https_response_with_json(username, password, url):
    # URL validation
    if 'https' in url:
        print('FOR DEBUG>>> Using HTTPS. GET from : ' + url)
    else:
        print('FOR DEBUG>>> URL seems to be wrong with : ' + url)
        # TODO: Specify Exception if wrong URL
        raise Exception

    # Initialize return value
    r = None

    # Run HTTP/HTTPS GET
    try:
        # verify=False for ignore SSL Certificate
        r = requests.get(url, auth=(username, password), verify=False)
        if r.status_code == 200:
            print('DEBUG>>> Return code 200, seems that Successfully GET content.')
            return r.text
        else:
            print('DEBUG>>> Return code is not 200, Check the connectivity or credentials...')
    except Exception as e:
        print('DEBUG>>> Some Error occurred when getting HTTP/HTTPS response.')
        print('Errors : ', e.args)
        return None
    else:
        return None


def convert_to_json():
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