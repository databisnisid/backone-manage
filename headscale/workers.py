from .models import HS_Users, HS_Nodes, HS_Preauthkeys
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from connectors.drivers.headscale import Headscale
from config.utils import to_list


def sync_hs_preauthkeys(hs_user):
    hs = Headscale(settings.HEADSCALE_URI, settings.HEADSCALE_KEY)
    result = hs.get_preauth_keys(hs_user.name)
    
    print(result)

    try:
        authkeys = result['preAuthKeys']

        for authkey in authkeys:
            try:
                hs_authkey = HS_Preauthkeys.objects.get(
                        hs_user=hs_user,
                        key=authkey['key']
                        )
                hs_authkey.is_reusable=authkey['reusable']
                hs_authkey.is_ephemeral=authkey['ephemeral']
                hs_authkey.is_used=authkey['used']
                hs_authkey.save()

            except ObjectDoesNotExist:
                hs_authkey = HS_Preauthkeys.objects.create(
                        id=authkey['id'],
                        hs_user=hs_user,
                        key=authkey['key'],
                        is_reusable=authkey['reusable'],
                        is_ephemeral=authkey['ephemeral'],
                        is_used=authkey['used'],
                        expiration=authkey['expiration'],
                        created_at=authkey['createdAt']
                        )

    except KeyError:
        pass


def sync_hs_users():
    hs = Headscale(settings.HEADSCALE_URI, settings.HEADSCALE_KEY)
    result = hs.get_users()

    print(result)

    try:
        users = result['users']

        for user in users:
            print(user)

            try:
                hs_user = HS_Users.objects.get(name=user['name'])

            except ObjectDoesNotExist:
                print('Creating User: ', user['name'])
                hs_user = HS_Users.objects.create(
                        id=user['id'],
                        name=user['name'],
                        created_at=user['createdAt']
                        )

            sync_hs_preauthkeys(hs_user)

    except KeyError:
        pass


def sync_hs_nodes():
    hs = Headscale(settings.HEADSCALE_URI, settings.HEADSCALE_KEY)
    result = hs.get_nodes()

    print(result)

    try:
        nodes = result['nodes']

        for node in nodes:
            print(node)
            node_user = node['user']

            try:
                #hs_node = HS_Nodes.objects.get(
                        #given_name=node['givenName'],
                        #)
                hs_node = HS_Nodes.objects.get(
                        node_key=node['nodeKey'],
                        )
                #        disco_key=node['discoKey']
                #        )
                if hs_node.hs_user.name != node_user['name']:
                    hs_user = HS_Users.objects.get(name=node_user['name'])
                    hs_node.hs_user = hs_user

                hs_node.last_seen = node['lastSeen']
                hs_node.is_online = node['online']
                hs_node.expiry = node['expiry']
                hs_node.save()

            except ObjectDoesNotExist:

                try:
                    hs_user = HS_Users.objects.get(name=node_user['name'])

                    hs_node = HS_Nodes.objects.create(
                            id=node['id'],
                            hs_user=hs_user,
                            machine_key=node['machineKey'],
                            node_key=node['nodeKey'],
                            disco_key=node['discoKey'],
                            hostname=node['name'],
                            given_name=node['givenName'],
                            name=node['givenName'],
                            ipaddress_v4=node['ipAddresses'][0],
                            ipaddress_v6=node['ipAddresses'][1],
                            last_seen=node['lastSeen'],
                            last_update=node['lastSuccessfulUpdate'],
                            expiry=node['expiry'],
                            is_online=node['online'],
                            created_at=node['createdAt'],
                            )

                except ObjectDoesNotExist:
                    pass

    except KeyError:
        pass

