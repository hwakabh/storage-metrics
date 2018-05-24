import common_functions as common


def main():
    d = common.Common()
    # d.create_container('postgres')
    containers = d.get_containers(isall=True)
    print(containers)

    # # Stop container(if isremove=True, container would be destroyed)
    # d.kill_container('clever_wing', isremove=False)

    # # Stop and remove all containers
    # for ck in containers.keys():
    #     print(ck)
    #     d.kill_container(ck, isremove=True)


if __name__ == '__main__':
    main()