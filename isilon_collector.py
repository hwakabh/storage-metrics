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
        # TODO: Specify Exception if wrong URL
        print('ISILON_LOGGER>>> Exception is throwed by common function. '
              'Error when getting information from Isilon ...')


def main():
    print('ISILON_LOGGER>>> Isilon Collector boots up...!!')

    # Setting parameters for target Isilon
    str_ipaddress = param.isilon_address
    str_username = param.isilon_user
    str_password = param.isilon_pass

    # Getting General isilon Information
    # TODO: Considering Looping for the case of multiple isilon
    print('ISILON_LOGGER>>> Target Isilon : ' + str_ipaddress)
    print('ISILON_LOGGER>>> General Information : ')
    isilon_info = get_isilon_information(str_ipaddress, str_username, str_password)

    # Instantiate Collector Class with constructor
    isilon_collector = Collector(strmark='isilon')

    # Send message to rabbitmq
    isilon_collector.send_message('[tmp]Isilon_Start')

    # --- Run main task(capacity)
    # Create capacity table in postgres
    capacity_maps = {'clustername': 'varchar',
                     'timestamp': 'timestamp',
                     '"ifs.bytes.total"': 'bigint',
                     '"ifs.bytes.used"': 'bigint',
                     '"ifs.percent.used"': 'double precision',
                     '"ifs.bytes.free"': 'bigint',
                     '"ifs.percent.free"': 'double precision'
                     }
    c_columns = '('
    for k, v in capacity_maps.items():
        c_columns += k + ' ' + v + ','
    c_columns += ')'
    isilon_collector.create_table(type='capacity', columns=c_columns.replace(',)',')'))

    # add cluster_name and timestamp before applying https results
    # TODO: retrieve 'clustername' and 'timestamp' labels directly from capacity_maps
    c_results = {'clustername': isilon_info['name'],
                 'timestamp': datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

    # Get capacity information
    for i in capacity_maps:
        if ('clustername' in i) or ('timestamp' in i):
            pass
        else:
            uri = 'https://' + str_ipaddress + ':8080' + '/platform/1/statistics/current?key=' + i.replace('"','')
            ret = get_https_response_with_json(str_username, str_password, uri)
            c_results[i.replace('"','')] = ret['stats'][0]['value']
    print(c_results)

    # Insert capacity information to postgres
    isilon_collector.send_data_to_postgres(data=c_results, data_type='capacity')

    # --- Run main task(quota)
    # Create quota table in postgres
    quota_maps = {'clustername': 'varchar',
                 'timestamp': 'timestamp',
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
    # common.get_https_response_with_json()

    # Insert quota information to postgres
    # common.send_data_to_postgres()

    # --- Run main task(performance)
    # Create performance table in postgres
    performance_maps = {'clustername': 'varchar',
                 'timestamp': 'timestamp',
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

    # Send message to rabbitmq
    isilon_collector.send_message('[tmp]Isilon_END')

    print('ISILON_LOGGER>>> Isilon Collector has done its task...!!')


if __name__ == '__main__':
    main()