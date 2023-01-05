from members.models import Members
from mqtt.models import Mqtt
from django.core.exceptions import ObjectDoesNotExist
from connectors.drivers import mqtt

def cron_fix_inconsistent_online():
    '''
    To fix status Online in BackOne
    But not online in Mqtt
    '''
    members = Members.objects.all()
    command = '/usr/bin/mqtt_presence'

    for member in members:
        if member.is_online() and not member.is_mqtt_online():
            try:
                Mqtt.objects.get(member_id=member.member_id)
                mqtt.rcall_cmd(member.network.id, member.member_id, command)
            except ObjectDoesNotExist:
                pass


