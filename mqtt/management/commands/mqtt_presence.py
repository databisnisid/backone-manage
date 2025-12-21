import logging
from paho.mqtt import client as mqtt
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned
from mqtt.models import Mqtt
from members.models import Members

logger = logging.getLogger(__name__)


def on_connect(client, userdata, keepalive, bind_address):
    # print(client, userdata, flags, rc)
    client.subscribe(settings.MQTT_TOPIC_PRESENCE)


def on_message(client, userdata, message):
    current_time = timezone.now()
    msg = str(message.payload.decode("utf-8"))

    print(str(current_time), msg)
    logger.info(f"{msg}")
    mqtt_msg = msg.split(";")
    member_id = mqtt_msg[0][:50]  # max_length=50

    try:
        model = mqtt_msg[1][0:50]
    except IndexError:
        model = ""

    try:
        board_name = mqtt_msg[2][0:50]
    except IndexError:
        board_name = ""

    try:
        release_version = mqtt_msg[3][0:50]
    except IndexError:
        release_version = ""

    try:
        release_target = mqtt_msg[4][0:50]
    except IndexError:
        release_target = ""

    try:
        ipaddress = mqtt_msg[5]
    except IndexError:
        ipaddress = ""

    try:
        is_rcall = True if int(mqtt_msg[6]) > 0 else False
    except (IndexError, ValueError) as error:
        is_rcall = False

    try:
        uptime = mqtt_msg[7][:100]  # max_length=100
    except IndexError:
        uptime = None

    try:
        serialnumber = mqtt_msg[8][:100]
    except IndexError:
        serialnumber = None

    try:
        num_core = int(mqtt_msg[9]) if mqtt_msg[9] else 1
    # except IndexError or ValueError:
    except IndexError:
        num_core = 1

    # Memory Usage
    try:
        mqtt_msg[10]
        memory_usage = float(mqtt_msg[10]) if mqtt_msg[10] else 0.0
    except IndexError:
        memory_usage = 0.0

    # Packet Loss
    try:
        mqtt_msg[11]
        packet_loss_string = mqtt_msg[11][:100]  # max_length=100
    except IndexError:
        packet_loss_string = None

    # Round Trip
    try:
        mqtt_msg[12]
        round_trip_string = mqtt_msg[12][:100]  # max_length=100
    except IndexError:
        round_trip_string = None

    # Switch Port UP
    try:
        mqtt_msg[13]
        switchport_up = mqtt_msg[13][:20]  # max_length=20
    except IndexError:
        switchport_up = None

    # Port Status
    try:
        mqtt_msg[14]
        port_status = mqtt_msg[14][:200]  # max_length=200
    except IndexError:
        port_status = None

    # Quota VNSTAT
    try:
        mqtt_msg[15]
        quota_vnstat = mqtt_msg[15][:200]  # max_length=200
    except IndexError:
        quota_vnstat = None

    # Tailscale IP Address
    try:
        mqtt_msg[16]
        ipaddress_ts = mqtt_msg[16]
    except IndexError:
        ipaddress_ts = None
    # print(member_id, model, board_name, release_version, release_target, ipaddress)
    # WAF
    try:
        mqtt_msg[17]
        is_waf = True if int(mqtt_msg[17]) > 0 else False
    except (IndexError, ValueError) as error:
        is_waf = False
    # print(member_id, model, board_name, release_version, release_target, ipaddress)

    # RSSI SIGNAL
    try:
        mqtt_msg[18]
        rssi_signal = int(mqtt_msg[18]) if mqtt_msg[18] else 99999
    # except IndexError or ValueError:
    except IndexError:
        rssi_signal = 99999

    # Hostname
    try:
        mqtt_msg[19]
        hostname = mqtt_msg[19]
    except IndexError:
        hostname = None

    try:
        mqtt_msg[20]
        netify_uuid = mqtt_msg[20]
    except IndexError:
        netify_uuid = None

    # Insert Into DB
    try:
        mqtt_member = Mqtt.objects.get(member_id=member_id)

    except ObjectDoesNotExist:
        mqtt_member = Mqtt()
        mqtt_member.member_id = member_id

    except MultipleObjectsReturned:
        Mqtt.objects.filter(member_id=member_id).delete()
        mqtt_member = Mqtt()
        mqtt_member.member_id = member_id

    mqtt_member.netify_uuid = netify_uuid
    mqtt_member.hostname = hostname
    mqtt_member.model = model
    mqtt_member.board_name = board_name
    mqtt_member.release_version = release_version
    mqtt_member.release_target = release_target
    mqtt_member.ipaddress = ipaddress
    mqtt_member.is_rcall = is_rcall
    mqtt_member.uptime = uptime
    mqtt_member.serialnumber = serialnumber
    mqtt_member.num_core = num_core
    mqtt_member.memory_usage = memory_usage
    mqtt_member.packet_loss_string = packet_loss_string
    mqtt_member.round_trip_string = round_trip_string
    mqtt_member.switchport_up = switchport_up
    mqtt_member.port_status = port_status
    mqtt_member.quota_vnstat = quota_vnstat
    mqtt_member.ipaddress_ts = ipaddress_ts
    mqtt_member.is_waf = is_waf
    mqtt_member.rssi_signal = rssi_signal
    mqtt_member.save()

    # members = Members.objects.filter(member_id=member_id, mqtt=None)
    members = Members.objects.filter(member_id=member_id)

    for member in members:
        if member.mqtt:
            if member.mqtt.member_id != mqtt_member.member_id:
                member.mqtt = mqtt_member
                member.is_waf = mqtt_member.is_waf
                member.save()
            else:
                member.is_waf = mqtt_member.is_waf
                member.save()
        else:
            member.mqtt = mqtt_member
            member.is_waf = mqtt_member.is_waf
            member.save()

    """
    members = Members.objects.filter(member_id=member_id)
    for member in members:
        if member.serialnumber != serialnumber:
            member.serialnumber = serialnumber
            member.save()
    """


class Command(BaseCommand):
    help = "Daemon to receive MQTT Presence Message"

    def handle(self, *args, **options):

        client = mqtt.Client()
        client.username_pw_set(settings.MQTT_USER, settings.MQTT_PASS)
        client.on_connect = on_connect
        client.on_message = on_message

        client.connect(settings.MQTT_HOST, int(settings.MQTT_PORT))
        client.loop_forever()
