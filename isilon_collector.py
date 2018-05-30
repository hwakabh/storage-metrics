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
    isilon_collector = Collector(strmark='ISILON')

    # Send message to rabbitmq
    isilon_collector.send_message('[tmp]Isilon_Start')

    # --- Run main task(capacity)
    # Create capacity table in postgres
    capacity_columns = '(cluster_name varchar' + \
                       ', timestamp timestamp' + \
                       ', ifs_bytes_total bigint' + \
                       ', ifs_bytes_used bigint' + \
                       ', ifs_percent_used double precision' + \
                       ', ifs_bytes_free bigint' + \
                       ', ifs_percent_free double precision)'
    isilon_collector.create_capacity_table(capacity_columns)

    # add cluster_name and timestamp before applying https results
    c_results = {}
    c_results['cluster_name'] = isilon_info['name']
    c_results['timestamp'] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Get capacity information
    capacity_keys = ('ifs.bytes.total', 'ifs.bytes.used', 'ifs.percent.used', 'ifs.bytes.free', 'ifs.percent.free', )
    for k in capacity_keys:
        uri = 'https://' + str_ipaddress + ':8080' + '/platform/1/statistics/current?key=' + k
        ret = get_https_response_with_json(str_username, str_password, uri)
        c_results[k] = ret['stats'][0]['value']
    print(c_results)

    # Insert capacity information to postgres
    isilon_collector.send_data_to_postgres(c_results)

    # --- Run main task(quota)
    # Create quota table in postgres
    quota_columns = '(qid varchar, qusername varchar, qpassword varchar)'
    isilon_collector.create_quota_table(quota_columns)

    # Get quota information
    # common.get_https_response_with_json()

    # Insert quota information to postgres
    # common.send_data_to_postgres()

    # --- Run main task(performance)
    # Create performance table in postgres
    perf_columns = '(pfid varchar, pfsername varchar, pfpassword varchar)'
    isilon_collector.create_performance_table(perf_columns)

    # Get performance information
    # common.get_https_response_with_json()

    # Insert performance information to postgres
    # common.send_data_to_postgres()

    # Send message to rabbitmq
    isilon_collector.send_message('[tmp]Isilon_END')

    print('ISILON_LOGGER>>> Isilon Collector has done its task...!!')


if __name__ == '__main__':
    main()