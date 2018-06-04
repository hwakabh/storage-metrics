from common_functions import Collector
from common_functions import get_https_response_with_json
import params as param
import datetime


def get_xtremio_information(ip, user, passwd):
    api = 'https://' + ip + '/api/json/v2/types/clusters'
    try:
        # Execute HTTPS GET
        ret = get_https_response_with_json(user, passwd, api)
    except Exception:
        print('XTREMIO_LOGGER>>> Exception is throwed by common function. '
          'Error when getting information from XtremIO ...')
    else:
        # Currently only considering single cluster
        clustername = ret['clusters'][0]['name']
        print('ClusterName : ' + clustername)

        api = 'https://' + ip + '/api/json/v2/types/clusters?name=' + clustername
        ret = get_https_response_with_json(user, passwd, api)
        # Printing for debug
        print('S/N : ' + ret['content']['sys-psnt-serial-number'])
        print('XtremApp Software Version : ' + ret['content']['sys-sw-version'])
        print('Brick information : ')
        for b in ret['content']['brick-list']:
            print('Brick Name : ' + b[1] + ' <<BrickNo : ' + str(b[0]) + ', BrickId : ' + str(b[2]) + '>>')
    # Return results
        return ret


def main():
    print('XTREMIO_LOGGER>>> Isilon Collector boots up...!!')

    # Setting parameters for target Isilon
    str_ipaddress = param.xtremio_address
    str_username = param.xtremio_user
    str_password = param.xtremio_pass

    # Getting General isilon Information
    print('XTREMIO_LOGGER>>> Target XtremIO(XMS) : ' + str_ipaddress)
    print('XTREMIO_LOGGER>>> General Information : ')
    xtremio_info = get_xtremio_information(str_ipaddress, str_username, str_password)

    # Instantiate Collector Class with constructor
    xtremio_collector = Collector(strmark='xtremio')

    # # Send message to rabbitmq
    # xtremio_collector.send_message('[tmp]XtremIO_Start')

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
    xtremio_collector.create_table(type='capacity', columns=c_columns.replace(',)',')'))

    # Get capacity information
    c_results = {}
    for i in capacity_maps:
        if 'clustername' in i:
            c_results[i] = xtremio_info['content']['name']
        elif 'timestamp' in i:
            c_results[i] = datetime.datetime.now().strftime('%Y/%m/%d %H:%M:%S')
        else:
            c_results[i] = xtremio_info['content'][i.replace('_','-')]

    # Insert capacity information to postgres
    xtremio_collector.send_data_to_postgres(data=c_results, data_type='capacity')

    # #! Volume(XtremIO LUNs information)
    # uri = 'https://10.32.210.156/api/json/v2/types/volumes?cluster-name=XIO_S5&full=1&prop=name&prop=vol-size&prop=logical-space-in-use&prop=naa-name&prop=ancestor-vol-id&prop=lun-mapping-list'
    # ret = get_https_response_with_json(str_username, str_password, uri)
    # print(ret)

    # --- Run main task(performance: CPU)

    # --- Run main task(performance: IOPS/Latency/Data-eduction-ratio)

    # # Insert performance information to postgres
    # xtremio_collector.send_data_to_postgres(data=c_results, data_type='performance')

    # # Send message to rabbitmq
    # xtremio_collector.send_message('[tmp]XtremIO_END')

    print('XTREMIO_LOGGER>>> XtremIO Collector has done its task...!!')


if __name__ == '__main__':
    main()