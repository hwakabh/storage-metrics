# common functions for each collector
import pika
import requests
import json
import psycopg2
import logging
import params as param

# To hide InsecureRequesetWarning in prompt
import urllib3
from urllib3.exceptions import InsecureRequestWarning
urllib3.disable_warnings(InsecureRequestWarning)

logger = logging.getLogger(__name__)


# Postgres Class to handle in each function
class Postgres:
    def __init__(self, hostname, port, username, password, database):
        self.hostname = hostname
        self.port = port
        self.username = username
        self.password = password
        self.database = database

    def connect(self):
        self.connection = psycopg2.connect(host=self.hostname, user=self.username, password=self.password,
                                           dbname=self.database, port=self.port)
        self.connection.autocommit = True
        return self.connection

    def get_connection(self):
        return self.connection

    def disconnect(self):
        self.connection.close()


class Collector:
    def __init__(self, strmark):
        self.strmark = strmark

    def create_table(self, metric, columns):
        # Expected metric: capacity, quota, cpu bandwidth
        table_name = self.strmark + '_' + metric + '_table'
        logger.info(self.strmark.upper() + '_Collector>>> Creating ' + metric + ' table on Postgres ...')
        create_table(table_name, columns)
        logger.info(self.strmark.upper() + '_Collector>>> Creating ' + metric + ' table Done.')

    # RabbitMQ : each collector is 'Producer' and would 'publish(=Send)' message
    def send_message(self, msg):
        connection = pika.BlockingConnection(pika.ConnectionParameters(host=param.mq_address))
        return_value = False
        try:
            channel = connection.channel()
            # create channel to send message
            channel.queue_declare(queue=self.strmark)
            logger.info(self.strmark.upper() + '_Collector>>> Create channel ' + self.strmark + ' with RabbitMQ...')
            channel.basic_publish(exchange='', routing_key=self.strmark, body=msg)
            logger.info(self.strmark.upper() + '_Collector>>> Messaage \'' + msg + '\' successfully sent to ' + self.strmark)
            return_value = True
        except Exception as e:
            logger.error(self.strmark.upper() + '_Collector>>> Error when sending message ...')
            logger.error('Errors : ', e.args)
        finally:
            try:
                connection.close()
            except Exception as e:
                logger.error(self.strmark.upper() + '_Collector>>> Error when sending message ...')
                logger.error('Errors : ', e.args)
        return return_value

    def send_data_to_postgres(self, data, data_type):
        table_name = self.strmark + '_' + data_type + '_table'
        logger.info(self.strmark.upper() + '_Collector>>> Start sending data to ' + table_name + ' ...')
        # Instantiate Postgres
        pg = Postgres(hostname=param.pg_address, port=param.pg_ports[0],
                      username=param.pg_username, password=param.pg_password, database=param.pg_database)
        pg.connect()
        cur = pg.get_connection().cursor()

        if (data_type == 'capacity') or (data_type == 'cpu') or (data_type == 'bandwidth') or (data_type == 'cl_performance'):
                # Generate query to table inserted
            q = 'INSERT INTO ' + table_name + '('
            for k in data.keys():
                q += str(k) + ', '
            q += ') VALUES('
            for v in data.values():
                q += '\'' + str(v) + '\', '
            q += ')'
            # Execute query
            cur.execute(q.replace(', )', ')'))
        elif data_type == 'quota':
            for l in range(len(data['path'])):
                # Generate query to table inserted
                q = 'INSERT INTO ' + table_name + '('
                for k in data.keys():
                    q += str(k) + ', '
                q += ') VALUES('
                for v in data.values():
                    if type(v) is list:
                        q += '\'' + str(v[l]) + '\', '
                    else:
                        q += '\'' + str(v) + '\', '
                q += ')'
                # Execute query
                cur.execute(q.replace(', )', ')'))
        elif data_type == 'sc_performance':
            for l in range(len(data['cpu'])):
                # Generate query to table inserted
                q = 'INSERT INTO ' + table_name + '('
                for k in data.keys():
                    q += str(k) + ', '
                q += ') VALUES('
                for v in data.values():
                    if type(v) is list:
                        q += '\'' + str(v[l]) + '\', '
                    else:
                        q += '\'' + str(v) + '\', '
                q += ')'
                # Execute query
                cur.execute(q.replace(', )', ')'))
        else:
            logger.error(self.strmark.upper() + '_Collector>>> Data-Type specified seemed to be wrong, '
                                         'data-type expecting follows bellow: \n'
                                         '\t Isilon : [capacity, quota, cpu, bandwidth] \n'
                                         '\t XtremIO : [capacity, sc_performance, cl_performance] \n'
                  )
        pg.disconnect()
        logger.info(self.strmark.upper() + '_Collector>>> Sending data to ' + table_name + ' Done.')


def create_table(name, columns):
    # Instantiate Postgres
    pg = Postgres(hostname=param.pg_address, port=param.pg_ports[0],
                  username=param.pg_username, password=param.pg_password, database=param.pg_database)
    # Generate query
    q = 'CREATE TABLE IF NOT EXISTS ' + name + columns
    # Connect to postgres and run create query
    pg.connect()
    cur = pg.get_connection().cursor()
    cur.execute(q)
    pg.disconnect()


def run_sql_query():
    pass


# Utilities
def convert_to_json(rbody):
    js = ''
    try:
        js = json.loads(rbody)
    except Exception as e:
        logger.error('FOR_DEBUG>>> Some Error occurred when converting from String to JSON.')
        logger.error('Errors : ', e.args)
    return js


def get_https_response_with_json(username, password, url):
    # URL validation
    if 'http' in url:
        logger.info('FOR DEBUG>>> Using HTTP/HTTPS. Checking for Secure connection or not...')
        if 'https' in url:
            logger.info('FOR DEBUG>>> Using HTTPS. GET from : ' + url)
        else:
            logger.info('FOR DEBUG>>> Using HTTP. GET from : ' + url)
    else:
        logger.error('FOR DEBUG>>> URL seems to be wrong with : ' + url)
        raise Exception

    rbody = ''
    # Run HTTP/HTTPS GET
    try:
        # verify=False for ignore SSL Certificate
        r = requests.get(url, auth=(username, password), verify=False)
        logger.info('FOR_DEBUG>>> Return code fine, seems that Successfully GET content.')
        rbody = r.text
    except Exception as e:
        logger.error('FOR_DEBUG>>> Some Error occurred when getting HTTP/HTTPS response.')
        logger.error('Errors : ', e.args)

    return convert_to_json(rbody)
