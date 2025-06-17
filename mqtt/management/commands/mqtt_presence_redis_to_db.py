from django.db.utils import IntegrityError
import redis
import json
from paho.mqtt import client as mqtt
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned
from mqtt.models import MqttRedis
from members.models import Members


class Command(BaseCommand):
    help = "Daemon to store message from Redis -> DB"

    def handle(self, *args, **options):

        r = redis.Redis(
            host=settings.MQTT_REDIS_HOST,
            port=settings.MQTT_REDIS_PORT,
            db=settings.MQTT_REDIS_DB,
        )

        for key in r.scan_iter(f"{settings.MQTT_REDIS_PREFIX}:*"):
            key_string = key.decode()
            key_split = key_string.split(":")
            member_id = key_split[1]
            msg = r.get(key_string)

            member_count = Members.objects.filter(member_id=member_id).count()
            if member_count:
                try:
                    msg_string = msg.decode()
                    print(f"{key_string}-> {msg_string}")
                    msg_json = json.loads(msg_string)

                    try:
                        mr = MqttRedis.objects.get(member_id=key_string)
                        mr.message = msg_json["msg"]

                    # except IntegrityError:
                    except ObjectDoesNotExist:
                        mr = MqttRedis()
                        mr.member_id = key_string
                        mr.message = msg_json["msg"]

                    mr.save()

                except AttributeError:
                    pass
            else:
                MqttRedis.objects.filter(member_id=key_string).delete()
