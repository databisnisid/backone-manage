from .models import Controllers
from networks.models import Networks, NetworkRoutes
from members.models import Members, MemberPeers
from .backend import Zerotier
from django.core.exceptions import ObjectDoesNotExist
from config.utils import to_list
from config.utils import get_user
from django.utils.timezone import localtime



def zt_import_members_delete(network):
    """
    This is for first time when importing the controllers
    Call by zt_import_networks()
    :param network:
    :return:
    """
    zt = Zerotier(network.controller.uri, network.controller.token)

    '''
    zt = Zerotier(network.controller.uri, network.controller.token)
    zt_members = zt.list_members(network.network_id)
    db_members = Members.objects.filter(network=network,
                                        configuration=None).values_list('member_id', flat=True)
    zt_members = to_list(zt_members)
    db_members = to_list(db_members)
    # print('ZT: ', zt_members)
    # print('DB: ', db_members)
    new_members = set(zt_members) ^ set(db_members)
    '''

    members = zt.list_members(network.network_id)

    for member in members:
        member_info = zt.get_member_info(network.network_id, member)
        """
        Only authorized member is imported
        """

        try:
            mem = Members.objects.get(member_id=member, network=network)
        except ObjectDoesNotExist:
            mem = Members()
            mem.name = 'NET-' + network.network_id + ' MEMBER-' +  member

        ip_address_list = ','.join([str(ip) for ip in member_info['ipAssignments']])
        mem.ipaddress = ip_address_list
        mem.member_id = member_info['id']
        mem.is_bridge = member_info['activeBridge']
        mem.is_no_auto_ip = member_info['noAutoAssignIps']
        mem.network = network
        #print(mem.member_id)
        mem.save()


def zt_import_members(network):
    """
    This is for first time when importing the controllers
    Call by zt_import_networks()
    :param network:
    :return:
    """
    zt = Zerotier(network.controller.uri, network.controller.token)

    '''
    zt = Zerotier(network.controller.uri, network.controller.token)
    zt_members = zt.list_members(network.network_id)
    db_members = Members.objects.filter(network=network,
                                        configuration=None).values_list('member_id', flat=True)
    zt_members = to_list(zt_members)
    db_members = to_list(db_members)
    # print('ZT: ', zt_members)
    # print('DB: ', db_members)
    new_members = set(zt_members) ^ set(db_members)
    '''

    members = zt.list_members(network.network_id)

    for member in members:
        member_info = zt.get_member_info(network.network_id, member)
        if member_info['authorized']:
            """
            Only authorized member is imported
            """

            try:
                mem = Members.objects.get(member_id=member, network=network)
            except ObjectDoesNotExist:
                mem = Members()
                mem.name = 'NET-' + network.network_id + ' MEMBER-' +  member

            ip_address_list = ','.join([str(ip) for ip in member_info['ipAssignments']])
            mem.ipaddress = ip_address_list
            mem.member_id = member_info['id']
            mem.is_bridge = member_info['activeBridge']
            mem.is_no_auto_ip = member_info['noAutoAssignIps']
            mem.network = network
            #print(mem.member_id)
            mem.save()


def zt_import_network_routes(network):
    """
    Call by zt_import_networks()
    :param network:
    :return:
    """
    zt = Zerotier(network.controller.uri, network.controller.token)
    result = zt.get_network_info(network.network_id)
    #print(net.route)
    routes = result['routes']
    for route in routes:
        print(route)
        ip_target = route['target']
        via = route['via']
        try:
            NetworkRoutes.objects.get(network=network,
                                      ip_network=ip_target,
                                      gateway=via)
        except ObjectDoesNotExist:
            net_route = NetworkRoutes(network=network,
                                      ip_network=ip_target,
                                      gateway=via)
            net_route.save()


def zt_import_networks(controller):
    """
    Import all Networks
    Call by zt_import_all_controllers()
    :param controller:
    :return:
    """
    try:
        control = Controllers.objects.get(id=controller.id)
        is_control = True
    except ObjectDoesNotExist:
        is_control = False

    if is_control:

        zt = Zerotier(control.uri, control.token)
        networks = zt.list_networks()
        for network in networks:
            try:
                net = Networks.objects.get(network_id=network, controller=controller)
                is_network = True
            except ObjectDoesNotExist:
                net = Networks()
                net.controller = controller
                is_network = False

            net_info = zt.get_network_info(network)
            print(net_info)

            if 'routes' in net_info:
                routes = net_info['routes']
                route_indexes = []
                for i in range(len(routes)):
                    if routes[i]['via'] is None:
                        route_indexes.append(i)

                """ If route is found """
                # is_route_inserted = False
                if route_indexes:
                    ip_networks = []
                    for route_index in route_indexes:
                        ip_networks.append(routes[route_index]['target'])
                    print(ip_networks)
                    net.ip_address_networks = ",".join([str(ip) for ip in ip_networks])

            if not is_network:
                print('Network is NOT in database. Add network id into DB', network)
                net_info = zt.get_network_info(network)
                if not net_info['name']:
                    net.name = network + ' Network'
                else:
                    net.name = net_info['name']
                net.network_id = net_info['nwid']
                try:
                    net.user
                    if net.user is None:
                        net.user = get_user()
                except ObjectDoesNotExist:
                    net.user = get_user()

                net.save()

            # Import members
            zt_import_network_routes(net)
            zt_import_members(net)


def zt_import_all_controllers():
    """
    For importing all controllers
    :return:
    """
    controllers = Controllers.objects.all()
    for controller in controllers:
        zt_import_networks(controller)


def zt_synchronize_network(network):
    """
    Is it used? Please review!!!
    Scheduled job hourly
    Call by zt_synchronize_all_networks()
    :param network:
    :return:
    """
    zt = Zerotier(network.controller.uri, network.controller.token)
    zt_members = zt.list_members(network.network_id)
    db_members = Members.objects.filter(network=network,
                                        configuration=None).values_list('member_id', flat=True)
    zt_members = to_list(zt_members)
    db_members = to_list(db_members)
    # print('ZT: ', zt_members)
    # print('DB: ', db_members)
    new_members = set(zt_members) ^ set(db_members)
    if new_members:
        # print(new_members)
        for new_member in new_members:
            try:
                zt_members.index(new_member)
                try:
                    member = Members.objects.get(member_id=new_member,
                                                 is_authorized=True)
                    #member = Members.objects.get(member_id=new_member,
                                                 #is_authorized=True,
                                                 #network=network)
                    member.save()
                    print('Adding New Members :', new_member)
                except ObjectDoesNotExist:
                    pass

            except ValueError:
                pass


def zt_synchronize_all_networks():
    """
    Main cronjob to synchronize all networks
    :return:
    """
    networks = Networks.objects.all()
    for network in networks:
        zt_synchronize_network(network)


def zt_synchronize_member_peers(network=None):
    """
    Syncronize Member Peer per Network
    Scheduled cronjob every 5 minutes
    :return:
    """
    print(localtime(), 'START - Synchronize Member Peers')
    if network is not None:
        member_peers = MemberPeers.objects.filter(network=network)
    else:
        member_peers = MemberPeers.objects.all()

    for member_peer in member_peers:
        zt = Zerotier(member_peer.network.controller.uri, member_peer.network.controller.token)
        member_peer.peers = zt.get_member_peers(member_peer.member_id)
        member_peer.save()
    print(localtime(), 'DONE - Synchronize Member Peers')


def zt_check_member_peers(member):
    """
    Update Member Peers
    """
    if member.peers is None:
        try:
            member_peer = MemberPeers.objects.get(member_id=member.member_id)
        except ObjectDoesNotExist:
            member_peer = MemberPeers()
            zt = Zerotier(member.network.controller.uri, member.network.controller.token)
            member_peer.peers = zt.get_member_peers(member_peer.member_id)
            member_peer.network = member.network
            member_peer.save()

        member.peers = member_peer
        member.save()


def zt_check_all_member_peers():
    """
    Update All Members Peers
    Running from crontab
    """
    print(localtime(), 'START - Checking All Member Peers')
    members = Members.objects.filter(peers=None)
    #members = Members.objects.all()
    for member in members:
        zt_check_member_peers(member)
    print(localtime(), 'END - Checking All Member Peers')
