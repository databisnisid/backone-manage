from paho.mqtt import client as mqtt
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from mqtt.models import Mqtt
from members.models import Members


def on_connect(client, userdata, keepalive, bind_address):
    #print(client, userdata, flags, rc)
    client.subscribe(settings.MQTT_TOPIC_PRESENCE)

def on_message(client, userdata, message):
    current_time = timezone.now()
    msg = str(message.payload.decode("utf-8"))
    print(str(current_time) ,msg)
    mqtt_msg = msg.split(';')
    member_id = mqtt_msg[0]
    model = mqtt_msg[1]
    board_name = mqtt_msg[2]
    release_version = mqtt_msg[3]
    release_target = mqtt_msg[4]
    ipaddress = mqtt_msg[5]

    try:
        is_rcall = True if int(mqtt_msg[6]) > 0 else False
    except IndexError:
        is_rcall = False

    try:
        uptime = mqtt_msg[7]
    except IndexError:
        uptime = None

    try:
        serialnumber = mqtt_msg[8]
    except IndexError:
        serialnumber = None

    try:
        num_core = int(mqtt_msg[9])
    except IndexError or ValueError:
        num_core = 1

    try:
        memory_usage = float(mqtt_msg[10])
    except IndexError or ValueError:
        memory_usage = 0.0

    #print(member_id, model, board_name, release_version, release_target, ipaddress)

    try:
        mqtt_member = Mqtt.objects.get(member_id=member_id)

    except ObjectDoesNotExist:
        mqtt_member = Mqtt()
        mqtt_member.member_id = member_id

    is_save = False

    if mqtt_member.model != model:
        mqtt_member.model = model
        is_save = True

    if mqtt_member.board_name != board_name:
        mqtt_member.board_name = board_name
        is_save = True

    if mqtt_member.release_version != release_version:
        mqtt_member.release_version = release_version
        is_save = True

    if mqtt_member.release_target != release_target:
        mqtt_member.release_target = release_target
        is_save = True

    if mqtt_member.ipaddress != ipaddress:
        mqtt_member.ipaddress = ipaddress
        is_save = True

    if mqtt_member.is_rcall != is_rcall:
        mqtt_member.is_rcall = is_rcall
        is_save = True

    if mqtt_member.uptime != uptime:
        mqtt_member.uptime = uptime
        is_save = True

    if mqtt_member.serialnumber != serialnumber:
        mqtt_member.serialnumber = serialnumber
        is_save = True

    if mqtt_member.num_core != num_core:
        mqtt_member.num_core = num_core
        is_save = True

    if mqtt_member.memory_usage != memory_usage:
        mqtt_member.memory_usage = memory_usage
        is_save = True

    if is_save:
        mqtt_member.save()

    members = Members.objects.filter(member_id=member_id)
    for member in members:
        if member.serialnumber != serialnumber:
            member.serialnumber = serialnumber
            member.save()


class Command(BaseCommand):
    help = 'Daemon to receive MQTT Presence Message'

    def handle(self, *args, **options):

        client = mqtt.Client()
        client.username_pw_set(settings.MQTT_USER, settings.MQTT_PASS)
        client.on_connect = on_connect
        client.on_message = on_message

        client.connect(settings.MQTT_HOST, int(settings.MQTT_PORT))
        client.loop_forever()

