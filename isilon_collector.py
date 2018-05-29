import common_functions as common
import params as param


def get_isilon_informations():
    pass


def main():
    print('ISILON_LOGGER>>> Isilon Collector boots up...!!')

    # Setting parameters for target Isilon
    # TODO: Considering Looping for the case of multiple isilon
    str_ipaddress = param.isilon_address
    str_username = param.isilon_user
    str_password = param.isilon_pass
    print('ISILON_LOGGER>>> Target Isilon : ' + str_ipaddress)

    # Send message to rabbitmq
    common.send_message('[tmp]Start')

    # --- Run main task(capacity)
    # Get capacity information
    common.get_http_response()

    # Create capacity table in postgres
    common.create_table()

    # Insert capacity information to postgres
    common.send_data_to_postgres()

    # --- Run main task(quota)
    # Get quota information
    common.get_http_response()

    # Create quota table in postgres
    common.create_table()

    # Insert quota information to postgres
    common.send_data_to_postgres()

    # --- Run main task(performance)
    # Get performance information
    common.get_http_response()

    # Create performance table in postgres
    common.create_table()

    # Insert performance information to postgres
    common.send_data_to_postgres()

    # Send message to rabbitmq
    common.send_message('[tmp]End')

    print('ISILON_LOGGER>>> Isilon Collector has done its task...!!')


if __name__ == '__main__':
    main()