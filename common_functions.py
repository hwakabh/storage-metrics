# common functions for each collector
import pika
import requests
import json
import params as param

# To hide InsecureRequesetWarning in prompt
import urllib3
from urllib3.exceptions import InsecureRequestWarning
urllib3.disable_warnings(InsecureRequestWarning)


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


def convert_to_json(rbody):
    js = ''
    try:
        js = json.loads(rbody)
    except Exception as e:
        print('FOR_DEBUG>>> Some Error occurred when converting from String to JSON.')
        print('Errors : ', e.args)
    return js


def get_https_response_with_json(username, password, url):
    # URL validation
    if 'https' in url:
        print('FOR DEBUG>>> Using HTTPS. GET from : ' + url)
    else:
        print('FOR DEBUG>>> URL seems to be wrong with : ' + url)
        # TODO: Specify Exception if wrong URL
        raise Exception

    rbody = ''
    # Run HTTP/HTTPS GET
    try:
        # verify=False for ignore SSL Certificate
        r = requests.get(url, auth=(username, password), verify=False)
        print('FOR_DEBUG>>> Return code 200, seems that Successfully GET content.')
        rbody = r.text
    except Exception as e:
        print('FOR_DEBUG>>> Some Error occurred when getting HTTP/HTTPS response.')
        print('Errors : ', e.args)

    return convert_to_json(rbody)


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