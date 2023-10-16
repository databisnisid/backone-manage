import requests
from members.models import Members
from django.conf import settings
from members.models import Members
#from mqtt.models import Mqtt
from .models import Mqtt
from django.core.exceptions import MultipleObjectsReturned, ObjectDoesNotExist
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


def get_quota():
    members = Members.objects.exclude(mobile_number_first__isnull=True)

    for member in members:
        #msisdn = member.mobile_number_first.replace
        response = requests.get(
                settings.DATA_URI_QUOTA + member.mobile_number_first[2:])
        response_json = response.json()

        print(response_json)

        quota_record = '{}'
        try:
            quota_record = response_json[0]

        except IndexError:
            pass

        try:
            try:
                quota_total = quota_record['quota_total'].replace(' ', '')
            except AttributeError:
                quota_total = ''

            try:
                quota_current = quota_record['quota_current'].replace(' ', '')
            except AttributeError:
                quota_current = ''
            
            try:
                quota_day = quota_record['quota_day'].replace(' ', '')
            except AttributeError:
                quota_day = ''

            mqtt_quota_first_prev = quota_record['quota_prev'].replace(' ', '')

            mqtt_quota_first = '{}/{}/{}'.format(quota_current, quota_total, quota_day)
            try:
                mqtt = Mqtt.objects.get(member_id=member.member_id)
                mqtt.quota_first = mqtt_quota_first
                mqtt.quota_first_prev = mqtt_quota_first_prev
                mqtt.save()

            except ObjectDoesNotExist:
                mqtt = Mqtt(
                        member_id=member.member_id,
                        quota_first=mqtt_quota_first
                        )
                mqtt.save()
            except MultipleObjectsReturned:
                Mqtt.objects.filter(member_id=member.member_id).delete()
                mqtt = Mqtt(
                        member_id=member.member_id,
                        quota_first=mqtt_quota_first
                        )
                mqtt.save()

        except TypeError or KeyError:
            pass

