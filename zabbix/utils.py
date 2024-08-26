import random
from members.views import prepare_data
from members.models import Members
from .models import ZabbixNetworks
from connectors.drivers.zabbix import Zabbix
from django.conf import settings


def sync_member_inventory(network):

    members = Members.objects.filter(network=network)

    zabbix = Zabbix()

    for member in members:
        hostname = member.get_hostname()
        if hostname:
            try:
                point = member.location.split(';')
                result = point[1].split(' ')
                lng = result[0].replace('POINT(', '')
                lat = result[1].replace(')', '')
            except AttributeError:
                lat = settings.GEO_WIDGET_DEFAULT_LOCATION['lat'] + random.uniform(-0.0025, 0.0025)
                lng = settings.GEO_WIDGET_DEFAULT_LOCATION['lng'] + random.uniform(-0.0025, 0.0025)

            params = {
                    'inventory_mode': 1,
                    'inventory': {
                        'location': member.address,
                        'location_lat': lat[:16],
                        'location_lon': lng[:16]
                        }
                    }
            zabbix.host_update_inventory(hostname, params)

            



    


