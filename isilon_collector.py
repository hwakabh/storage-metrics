from common_functions import Collector
from common_functions import get_https_response_with_json
import params as param
import datetime


def get_isilon_information(ip, user, passwd):
    api = 'https://' + ip + ':8080' + '/platform/1/cluster/config'
    try:
        # Execute HTTPS GET
        ret = get_https_response_with_json(user, passwd, api)
        # Printing for debug
        print('S/N : ' + ret['local_serial'])
        print('Cluster Name : ' + ret['name'])
        print('OneFS Version : ' + ret['onefs_version']['release'] + ' <<Build : ' + ret['onefs_version']['build'] + '>>')
        print('Nodes count : ' + str(len(ret['devices'])))
        print('Nodes information : ')
        for d in ret['devices']:
            print('DeviceID : ' + str(d['devid']) + ' <<GUID : ' + d['guid'] + '>>')
        # Return result
        return ret
    except Exception:
        print('ISILON_LOGGER>>> Exception is throwed by common function. '
              'Error when getting information from Isilon ...')


def calculate_average(t, json):
    avg_sum = 0
    if t == 'cpu':
        for i in range(len(json['stats'])):
            sum = 0
            for v in json['stats'][i]['values']:
                e = v['value'] / 10
                sum = sum + e
            cpu_average_byid = 100 - (sum / len(json['stats'][i]['values']))
            print('ISILON_LOGGER>>> CPU Average Util on DeviceID-' + str(json['stats'][i]['devid']) + ' : ' + str(cpu_average_byid))
            avg_sum = avg_sum + cpu_average_byid
        cpu_average = avg_sum / len(json['stats'])
        print('ISILON_LOGGER>>> Average CPU Utilization : ' + str(cpu_average))
        return cpu_average
    elif t == 'bandwidth':
        for i in range(len(json['stats'])):
            sum = 0
            for v in json['stats'][i]['values']:
                sum = sum + v['value']
            bandwidth_average_byid = sum / len(json['stats'][i]['values'])
            print('ISILON_LOGGER>>> Average bandwidth Util on DeviceID-' + str(json['stats'][i]['devid']) + ' : ' + str(bandwidth_average_byid))
            avg_sum = avg_sum + bandwidth_average_byid
        bandwidth_average = avg_sum / len(json['stats'])
        print('ISILON_LOGGER>>> Bandwidth average Utilization : ' + str(bandwidth_average))
        return bandwidth_average
    else:
        print('Specified flag is wrong...')


def main():
    print('ISILON_LOGGER>>> Isilon Collector boots up...!!')

    # Setting parameters for target Isilon
    str_ipaddress = param.isilon_address
    str_username = param.isilon_user
    str_password = param.isilon_pass

    # Getting General isilon Information
    print('ISILON_LOGGER>>> Target Isilon : ' + str_ipaddress)
    print('ISILON_LOGGER>>> General Information : ')
    isilon_info = get_isilon_information(str_ipaddress, str_username, str_password)

    # Instantiate Collector Class with constructor
    isilon_collector = Collector(strmark='isilon')

    # # Send message to rabbitmq
    # isilon_collector.send_message('[tmp]Isilon_Start')

    # --- Run main task(capacity)
    # Create capacity table in postgres
    capacity_maps = {'clustername': 'varchar',
                     'timestamp': 'varchar',
                     'ifs_bytes_total': 'bigint',
                     'ifs_bytes_used': 'bigint',
                     'ifs_percent_used': 'double precision',
                     'ifs_bytes_free': 'bigint',
                     'ifs_percent_free': 'double precision'
                     }
    c_columns = '('
    for k, v in capacity_maps.items():
        c_columns += k + ' ' + v + ','
    c_columns += ')'
    isilon_collector.create_table(type='capacity', columns=c_columns.replace(',)',')'))

    # Get capacity information
    c_results = {}
    for i in capacity_maps:
        if 'clustername' in i:
            c_results[i] = isilon_info['name']
        elif 'timestamp' in i:
            c_results[i] = datetime.datetime.now().strftime('%Y/%m/%d %H:%M:%S')
        else:
            uri = 'https://' + str_ipaddress + ':8080' + '/platform/1/statistics/current?key=' + i.replace('_','.')
            ret = get_https_response_with_json(str_username, str_password, uri)
            c_results[i] = ret['stats'][0]['value']

    # Insert capacity information to postgres
    isilon_collector.send_data_to_postgres(data=c_results, data_type='capacity')

    # --- Run main task(quota)
    # Create quota table in postgres
    quota_maps = {'clustername': 'varchar',
                  'timestamp': 'varchar',
                  'path': 'varchar',
                  'hard_threshold': 'bigint',
                  'logical_with_overhead': 'bigint',
                  'physical_with_overhead': 'bigint'
                  }
    q_columns = '('
    for k, v in quota_maps.items():
        q_columns += k + ' ' + v + ','
    q_columns += ')'
    isilon_collector.create_table(type='quota', columns=q_columns.replace(',)',')'))

    # Get quota information
    uri = 'https://' + str_ipaddress + ':8080' + '/platform/1/quota/quotas'
    ret = get_https_response_with_json(str_username, str_password, uri)

    q_results = {}
    for i in quota_maps:
        value_list = []
        if 'clustername' in i:
            q_results[i] = isilon_info['name']
        elif 'timestamp' in i:
            q_results[i] = datetime.datetime.now().strftime('%Y/%m/%d %H:%M:%S')
        elif i == 'path':
            for v in ret['quotas']:
                value_list.append(v['path'])
                q_results[i] = value_list
        elif i == 'hard_threshold':
            for v in ret['quotas']:
                if v['thresholds']['hard'] is None:
                    value_list.append(0)
                else:
                    value_list.append(v['thresholds']['hard'])
                q_results[i] = value_list
        elif i == 'logical_with_overhead':
            for v in ret['quotas']:
                value_list.append(v['usage']['logical'])
                q_results[i] = value_list
        elif i == 'physical_with_overhead':
            for v in ret['quotas']:
                value_list.append(v['usage']['physical'])
                q_results[i] = value_list
        else:
            print('Some Errors...')

    # Insert capacity information to postgres
    isilon_collector.send_data_to_postgres(data=q_results, data_type='quota')

    # --- Run main task(performance: CPU/Bandwidth)
    # Get common prefix(CPU/bandwidth)
    uri_prefix = 'https://' + str_ipaddress + ':8080' + '/platform/1/statistics/history'

    # Create performance(CPU) table in postgres
    cpu_maps = {'clustername': 'varchar',
                'timestamp': 'varchar',
                'average_cpu': 'double precision'
                }
    cpu_columns = '('
    for k, v in cpu_maps.items():
        cpu_columns += k + ' ' + v + ','
    cpu_columns += ')'
    isilon_collector.create_table(type='cpu', columns=cpu_columns.replace(',)', ')'))

    # Get CPU information
    cpu_results = {}
    for i in cpu_maps:
        if 'clustername' in i:
            cpu_results[i] = isilon_info['name']
        elif 'timestamp' in i:
            cpu_results[i] = datetime.datetime.now().strftime('%Y/%m/%d %H:%M:%S')
        else:
            # add to cpu keys and get information about CPU
            uri_key_cpu = 'node.cpu.idle.avg&nodes=all'
            uri = uri_prefix + '?key=' + uri_key_cpu
            ret_cpu = get_https_response_with_json(str_username, str_password, uri)
            # Calculate daily CPu utilization
            daily_cpu_util = calculate_average('cpu', ret_cpu)
            cpu_results[i] = daily_cpu_util

    # Insert CPU information to postgres
    isilon_collector.send_data_to_postgres(data=cpu_results, data_type='cpu')

    # Create performance(bandwidth) table in postgres
    bandwidth_maps = {'clustername': 'varchar',
                      'timestamp': 'varchar',
                      'ext1_rdavg_day': 'double precision', 'ext1_wtavg_day': 'double precision',
                      'ext2_rdavg_day': 'double precision', 'ext2_wtavg_day': 'double precision',
                      'gb1_rdavg_day': 'double precision', 'gb1_wtavg_day': 'double precision',
                      'gb2_rdavg_day': 'double precision', 'gb2_wtavg_day': 'double precision'
                      }
    bandwidth_columns = '('
    for k, v in bandwidth_maps.items():
        bandwidth_columns += k + ' ' + v + ','
    bandwidth_columns += ')'
    isilon_collector.create_table(type='bandwidth', columns=bandwidth_columns.replace(',)',')'))

    # add to bandwidth keys and get information about bandwidth
    uri_keys_bandwidth = (
        'node.net.iface.bytes.out.rate.2',
        'node.net.iface.bytes.in.rate.2',
        'node.net.iface.bytes.out.rate.3',
        'node.net.iface.bytes.in.rate.3',
        'node.net.iface.bytes.out.rate.4',
        'node.net.iface.bytes.in.rate.4',
        'node.net.iface.bytes.out.rate.5',
        'node.net.iface.bytes.in.rate.5'
    )

    # Get capacity information
    bandwidth_results = {}
    for i, v in enumerate(bandwidth_maps):
        if 'clustername' in v:
            bandwidth_results[v] = isilon_info['name']
        elif 'timestamp' in v:
            bandwidth_results[v] = datetime.datetime.now().strftime('%Y/%m/%d %H:%M:%S')
        else:
            uri = uri_prefix + '?key=' + uri_keys_bandwidth[i-2]
            ret_bandwidth = get_https_response_with_json(str_username, str_password, uri)
            bandwidth_results[v] = calculate_average('bandwidth', ret_bandwidth)

    # Insert capacity information to postgres
    isilon_collector.send_data_to_postgres(data=bandwidth_results, data_type='bandwidth')

    # # Send message to rabbitmq
    # isilon_collector.send_message('[tmp]Isilon_END')

    print('ISILON_LOGGER>>> Isilon Collector has done its task...!!')


if __name__ == '__main__':
    main()