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

    # --- Run main task(performance)
    # Create performance table in postgres
    performance_maps = {'clustername': 'varchar',
                        'timestamp': 'varchar',
                        'ext1_rdavg_day': 'double precision', 'ext1_wtavg_day': 'double precision',
                        'ext2_rdavg_day': 'double precision', 'ext2_wtavg_day': 'double precision',
                        'gb1_rdavg_day': 'double precision', 'gb1_wtavg_day': 'double precision',
                        'gb2_rdavg_day': 'double precision', 'gb2_wtavg_day': 'double precision'
                        }
    perf_columns = '('
    for k, v in performance_maps.items():
        perf_columns += k + ' ' + v + ','
    perf_columns += ')'
    isilon_collector.create_table(type='performance', columns=perf_columns.replace(',)',')'))

    # Get performance information
    # common.get_https_response_with_json()

    # Insert performance information to postgres
    # common.send_data_to_postgres()

    # # Send message to rabbitmq
    # isilon_collector.send_message('[tmp]Isilon_END')

    print('ISILON_LOGGER>>> Isilon Collector has done its task...!!')


if __name__ == '__main__':
    main()