import common_functions as common
import params as param

global str_ipaddress
global str_username
global str_password


def get_isilon_information(ip, user, passwd):
    uri = 'https://' + ip + ':8080' + '/platform/1/cluster/config'
    try:
        ret = common.get_https_response_with_json(user, passwd, uri)
        print('S/N : ' + ret['local_serial'])
        print('Cluster Name : ' + ret['name'])
        print('OneFS Version : ' + ret['onefs_version']['release'] + ' <<Build : ' + ret['onefs_version']['build'] + '>>')
        print('Nodes count : ' + str(len(ret['devices'])))
        print('Nodes information : ')
        for d in ret['devices']:
            print('DeviceID : ' + str(d['devid']) + ' <<GUID : ' + d['guid'] + '>>')
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
    # TODO: Considering Looping for the case of multiple isilon
    print('ISILON_LOGGER>>> Target Isilon : ' + str_ipaddress)
    print('ISILON_LOGGER>>> General Information : ')
    get_isilon_information(str_ipaddress, str_username, str_password)

    # Send message to rabbitmq
    common.send_message('[tmp]Isilon_Start')

    # --- Run main task(capacity)
    # Create capacity table in postgres
    common.create_table()

    # Get capacity information
    # common.get_https_response_with_json()

    # Insert capacity information to postgres
    common.send_data_to_postgres()

    # --- Run main task(quota)
    # Create quota table in postgres
    common.create_table()

    # Get quota information
    # common.get_https_response_with_json()

    # Insert quota information to postgres
    common.send_data_to_postgres()

    # --- Run main task(performance)
    # Create performance table in postgres
    common.create_table()

    # Get performance information
    # common.get_https_response_with_json()

    # Insert performance information to postgres
    common.send_data_to_postgres()

    # Send message to rabbitmq
    common.send_message('[tmp]Isilon_End')

    print('ISILON_LOGGER>>> Isilon Collector has done its task...!!')


if __name__ == '__main__':
    main()