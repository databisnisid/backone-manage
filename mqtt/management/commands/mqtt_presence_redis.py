import redis
from redis.exceptions import TimeoutError
from paho.mqtt import client as mqtt
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned
from config.settings import MQTT_REDIS_DB
from mqtt.models import Mqtt
from members.models import Members

"""
MQTT_REDIS_HOST
MQTT_REDIS_PORT
MQTT_REDIS_DB -> int default 0
MQTT_REDIS_SETEX -> int default 86400 = 24hour -> for r.setex()
"""
r = redis.Redis(
    host=settings.MQTT_REDIS_HOST,
    port=settings.MQTT_REDIS_PORT,
    db=MQTT_REDIS_DB,
    socket_timeout=1,
)


def on_connect(client, userdata, keepalive, bind_address):
    # print(client, userdata, flags, rc)
    client.subscribe(settings.MQTT_TOPIC_PRESENCE)


def on_message(client, userdata, message):
    current_time = timezone.now()
    msg = str(message.payload.decode("utf-8"))

    print(str(current_time), msg)
    mqtt_msg = msg.split(";")
    member_id = mqtt_msg[0][:50]  # max_length=50
    # r = redis.Redis()
    member_id_with_prefix = f"{settings.MQTT_REDIS_PREFIX}:{member_id}"
    timestamp = int(current_time.timestamp())
    # r.setex(member_id, settings.MQTT_REDIS_SETEX, msg)
    msg_json = {}
    msg_json["msg"] = msg
    msg_json["ts"] = timestamp
    msg_json_string = str(msg_json).replace("'", '"')
    # r.setex(member_id_with_prefix, settings.MQTT_REDIS_SETEX, msg)
    try:
        r.setex(member_id_with_prefix, settings.MQTT_REDIS_SETEX, msg_json_string)
    except TimeoutError:
        pass


class Command(BaseCommand):
    help = "Daemon to receive MQTT Presence Message -> Redis"

    def handle(self, *args, **options):

        client = mqtt.Client()
        client.username_pw_set(settings.MQTT_USER, settings.MQTT_PASS)
        client.on_connect = on_connect
        client.on_message = on_message

        client.connect(settings.MQTT_HOST, int(settings.MQTT_PORT))
        client.loop_forever()
