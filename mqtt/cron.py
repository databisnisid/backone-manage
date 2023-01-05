from members.models import Members
from mqtt.models import Mqtt
from django.core.exceptions import ObjectDoesNotExist
from connectors.drivers import mqtt, ping
from controllers.workers import zt_check_member_peers

def fix_inconsistent_online():
    '''
    To fix status Online in BackOne
    But not online in Mqtt
    '''
    members = Members.objects.all()
    command = '/usr/bin/mqtt_presence'

    for member in members:
        if member.is_online() and not member.is_mqtt_online():
            if ping.ping(member.ipaddress):
                try:
                    Mqtt.objects.get(member_id=member.member_id)
                    mqtt.rcall_cmd(member.network.network_id, member.member_id, command)
                except ObjectDoesNotExist:
                    pass
            else:
                zt_check_member_peers(member)

