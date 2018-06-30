import datetime
import logging

from common_functions import Collector
from common_functions import get_https_response_with_json
import params as param

logfilename = './logs/' + datetime.datetime.now().strftime('%Y%m%d_xtremio_collector') + ".log"
# logging.basicConfig()
_detail_formatting = '%(asctime)s : %(name)s - %(levelname)s : %(message)s'
logging.basicConfig(level=logging.DEBUG, format=_detail_formatting, filename=logfilename, )
logging.getLogger('modules').setLevel(level=logging.DEBUG)

console = logging.StreamHandler()
console_formatter = logging.Formatter('%(asctime)s : %(message)s')
console.setFormatter(console_formatter)
console.setLevel(logging.INFO)
logging.getLogger('modules').addHandler(console)

logger = logging.getLogger(__name__)
logging.getLogger(__name__).addHandler(console)



def get_xtremio_information(ip, user, passwd):
    api = 'https://' + ip + '/api/json/v2/types/clusters'
    try:
        # Execute HTTPS GET
        ret = get_https_response_with_json(user, passwd, api)
    except Exception:
        logger.info('XtremIO_Collector>>> Exception is throwed by common function. '
              'Error when getting information from XtremIO ...')
    else:
        # Currently only considering single cluster
        clustername = ret['clusters'][0]['name']
        logger.info('ClusterName : ' + clustername)

        api = 'https://' + ip + '/api/json/v2/types/clusters?name=' + clustername
        ret = get_https_response_with_json(user, passwd, api)
        # Printing for debug
        logger.info('S/N : ' + ret['content']['sys-psnt-serial-number'])
        logger.info('XtremApp Software Version : ' + ret['content']['sys-sw-version'])
        logger.info('StorageController Count(xenv count) : ' + str(ret['content']['num-of-xenvs']))
        logger.info('Brick information : ')
        for b in ret['content']['brick-list']:
            logger.info('Brick Name : ' + b[1] + ' <<BrickNo : ' + str(b[0]) + ', BrickId : ' + str(b[2]) + '>>')
    # Return results
        return ret


def get_xtremio_performance_uri(ip, entity, property):
    now = datetime.datetime.now()
    yesterday = now - datetime.timedelta(days=1)

    uri = 'https://' + ip + '/api/json/v2/types/performance?' + \
          'entity=' + entity + '&prop=' + property + '&granularity=one_hour' + \
          '&from-time=' + str(yesterday.strftime('%Y-%m-%d+%H:%M:%S')) + '&to-time=' + str(now.strftime('%Y-%m-%d+%H:%M:%S'))
    return uri


def calculate_xenv_cpu_utilization(json, sc_count):
    sc_map = {}
    # Get all xenv name-list
    scs = []
    for sc in json['counters']:
        scs.append(sc[2])
    # Deduplicate with xenv name
    uniq_sc = sorted(list(dict.fromkeys(scs)))

    for c in range(int(sc_count)):
        utils = [util[4] for util in json['counters'] if util[3] == (c+1)]
        average_xenv_cpu_util = sum(utils) / len(utils)
        # print('Average xenv_cpu_util of ' + uniq_sc[c] + ' = ' + str(average_xenv_cpu_util) )
        sc_map[str(uniq_sc[c])] = average_xenv_cpu_util

    return sc_map


# Calculation for Cluster IOPS/Latency/Data-eduction-ratio
def calculate_cluster_performances(json):
    sum = 0
    for cl in json['counters']:
        sum += cl[4]
    average_value = sum / len(json['counters'])
    return average_value


def main():
    logger.info('XtremIO_Collector>>> Xtrem Collector boots up...!!')

    # Setting parameters for target Isilon
    str_ipaddress = param.xtremio_address
    str_username = param.xtremio_user
    str_password = param.xtremio_pass

    # Getting General isilon Information
    logger.info('XtremIO_Collector>>> Target XtremIO(XMS) : ' + str_ipaddress)
    logger.info('XtremIO_Collector>>> General Information : ')
    xtremio_info = get_xtremio_information(str_ipaddress, str_username, str_password)

    # Instantiate Collector Class with constructor
    xtremio_collector = Collector(strmark='xtremio')

    # Send message to rabbitmq
    xtremio_collector.send_message('Start')

    # --- Run main task(capacity)
    # Create capacity table in postgres
    capacity_maps = {'clustername': 'varchar',
                     'timestamp': 'varchar',
                     'logical_space_in_use': 'bigint',
                     'ud_ssd_space_in_use': 'bigint',
                     'ud_ssd_space': 'bigint',
                     'data_reduction_ratio': 'double precision'
                     }
    c_columns = '('
    for k, v in capacity_maps.items():
        c_columns += k + ' ' + v + ','
    c_columns += ')'
    xtremio_collector.create_table(metric='capacity', columns=c_columns.replace(',)',')'))

    clustername = xtremio_info['content']['name']
    # Get capacity information
    c_results = {}
    for i in capacity_maps:
        if 'clustername' in i:
            c_results[i] = clustername
        elif 'timestamp' in i:
            c_results[i] = datetime.datetime.now().strftime('%Y/%m/%d %H:%M:%S')
        else:
            c_results[i] = xtremio_info['content'][i.replace('_','-')]

    # Insert capacity information to postgres
    xtremio_collector.send_data_to_postgres(data=c_results, data_type='capacity')

    # #! Volume(XtremIO LUNs information)
    # uri = 'https://10.32.210.156/api/json/v2/types/volumes?cluster-name=XIO_S5&full=1
    # &prop=name&prop=vol-size&prop=logical-space-in-use&prop=naa-name&prop=ancestor-vol-id&prop=lun-mapping-list'
    # ret = get_https_response_with_json(str_username, str_password, uri)
    # print(ret)

    # --- Run main task(performance: CPU)
    # Create StorageController Performance table in postgres
    sc_perf_maps = {'clustername': 'varchar',
                    'timestamp': 'varchar',
                    'cpu': 'varchar',
                    'avg__cpu_usage': 'double precision'
                   }
    sc_perf_columns = '('
    for k, v in sc_perf_maps.items():
        sc_perf_columns += k + ' ' + v + ','
    sc_perf_columns += ')'
    xtremio_collector.create_table(metric='sc_performance', columns=sc_perf_columns.replace(',)',')'))

    # Get avg__cpu_usage by StorageController
    uri = get_xtremio_performance_uri(ip=str_ipaddress, entity='XEnv', property='avg__cpu_usage')
    ret = get_https_response_with_json(str_username, str_password, uri)

    # Calculate avg__cpu_usage by StorageController
    average_xenv_cpu_utils = calculate_xenv_cpu_utilization(ret, xtremio_info['content']['num-of-xenvs'])

    # Get xenv average cpu utilization information
    sc_perf_results = {}
    for i in sc_perf_maps:
        value_list = []
        if 'clustername' in i:
            sc_perf_results[i] = clustername
        elif 'timestamp' in i:
            sc_perf_results[i] = datetime.datetime.now().strftime('%Y/%m/%d %H:%M:%S')
        elif i == 'cpu':
            for k in average_xenv_cpu_utils.keys():
                value_list.append(k)
                sc_perf_results[i] = value_list
        elif i == 'avg__cpu_usage':
            for v in average_xenv_cpu_utils.values():
                value_list.append(v)
                sc_perf_results[i] = value_list
        else:
            logger.error('XtremIO_Collector>>> Some Errors...')

    # Insert avg__cpu usage to postgres
    xtremio_collector.send_data_to_postgres(data=sc_perf_results, data_type='sc_performance')

    # --- Run main task(performance: IOPS, Latency, Data-eduction-ratio)
    # Create Cluster Performance table in postgres
    cl_perf_maps = {'clustername': 'varchar',
                    'timestamp': 'varchar',
                    'avg__iops': 'double precision',
                    'avg__avg_latency': 'double precision',
                    'avg__data_reduction_ratio': 'double precision'
                    }
    cl_perf_columns = '('
    for k, v in cl_perf_maps.items():
        cl_perf_columns += k + ' ' + v + ','
    cl_perf_columns += ')'
    xtremio_collector.create_table(metric='cl_performance', columns=cl_perf_columns.replace(',)',')'))

    # Get performance information(IOPS, Latency, Data-eduction-ratio)
    cl_perf_results = {}
    for i in cl_perf_maps:
        if 'clustername' in i:
            cl_perf_results[i] = clustername
        elif 'timestamp' in i:
            cl_perf_results[i] = datetime.datetime.now().strftime('%Y/%m/%d %H:%M:%S')
        else:
            # Generate and GET response
            uri = get_xtremio_performance_uri(ip=str_ipaddress, entity='Cluster', property=i)
            ret = get_https_response_with_json(str_username, str_password, uri)
            # calculate averages
            avg_value = calculate_cluster_performances(ret)
            cl_perf_results[i] = avg_value

    # Insert capacity information to postgres
    xtremio_collector.send_data_to_postgres(data=cl_perf_results, data_type='cl_performance')

    # Send message to rabbitmq
    xtremio_collector.send_message('END')

    logger.info('XtremIO_Collector>>> XtremIO Collector has done its task...!!')


if __name__ == '__main__':
    main()