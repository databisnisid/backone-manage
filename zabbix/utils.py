import random
from members.views import prepare_data
from members.models import Members
from .models import ZabbixNetworks
from connectors.drivers.zabbix import Zabbix
from django.conf import settings


def sync_member_inventory(network, zabbix):

    members = Members.objects.filter(network=network)

    # zabbix = Zabbix()

    for member in members:
        print(f"Member: {member.name}")
        hostname = member.get_hostname()
        if hostname:
            print(f"Hostname: {hostname}")
            try:
                point = member.location.split(";")
                result = point[1].split(" ")
                lng = result[0].replace("POINT(", "")
                lat = result[1].replace(")", "")
            except AttributeError:
                lat = settings.GEO_WIDGET_DEFAULT_LOCATION["lat"] + random.uniform(
                    -0.0025, 0.0025
                )
                lng = settings.GEO_WIDGET_DEFAULT_LOCATION["lng"] + random.uniform(
                    -0.0025, 0.0025
                )

            if type(lat) != str:
                lat = str(lat)
            if type(lng) != str:
                lng = str(lng)

            params = {
                "name": member.name,
                "description": member.description,
                "inventory_mode": 1,
                "inventory": {
                    "alias": member.name[:128],
                    "location": member.address if member.address else "",
                    "location_lat": lat[:16],
                    "location_lon": lng[:16],
                    "model": member.model()[:64],
                    "hardware": member.board_name(),
                    "hw_arch": member.release_target()[:32],
                    "software": member.release_version(),
                    "serialno_a": member.serialnumber()[:64],
                    "serialno_b": member.serialnumber()[:64],
                    "poc_1_cell": (
                        member.mobile_number_first[:64]
                        if member.mobile_number_first
                        else ""
                    ),
                    "host_router": member.member_id,
                    "host_networks": member.network.name,
                },
            }
            result = zabbix.host_update_inventory(hostname, params)

            if not result:
                print(f"Host: {hostname} NOT found! Try to create it.")
                result = zabbix.host_create(hostname, params)
                print(f"Host '{hostname}' created with ID: {result['hostids'][0]}")


def sync_zabbix_networks():

    zabbix_networks = ZabbixNetworks.objects.all()

    for zabbix_network in zabbix_networks:
        networks = zabbix_network.networks.all()

        if zabbix_network.config:
            print("Use Zabbix Config")
            zabbix = Zabbix(zabbix_network.config.url, zabbix_network.config.token)
        else:
            print("Use Settings from settings.py")
            zabbix = Zabbix()

        for network in networks:
            sync_member_inventory(network, zabbix)
