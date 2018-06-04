from common_functions import Collector
from common_functions import get_https_response_with_json
import params as param


def get_xtremio_information(ip, user, passwd):
    api = 'https://' + ip + '/api/json/v2/types/clusters'
    try:
        # Execute HTTPS GET
        ret = get_https_response_with_json(user, passwd, api)
    except Exception:
        print('XTREMIO_LOGGER>>> Exception is throwed by common function. '
          'Error when getting information from XtremIO ...')
    else:
        clusters = []
        for c in range(len(ret['clusters'])):
            clusters.append(ret['clusters'][c]['name'])
            print('ClusterName : ' + clusters[c])

            api = 'https://' + ip + '/api/json/v2/types/clusters?name=' + clusters[c]
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
    # print(xtremio_info)


if __name__ == '__main__':
    main()