from django.core.exceptions import ObjectDoesNotExist
import redis
import json
from django.conf import settings
from .models import MqttRedis


def get_msg_redis(member_id: str):
    r = redis.Redis(
        host=settings.MQTT_REDIS_HOST,
        port=settings.MQTT_REDIS_PORT,
        db=settings.MQTT_REDIS_DB,
    )
    member_id_prefix = f"{settings.MQTT_REDIS_PREFIX}:{member_id}"
    # msg = r.get(str(f"{settings.MQTT_REDIS_PREFIX}:{member_id}"))
    msg = r.get(member_id_prefix)
    try:
        msg_decode = msg.decode()
        msg_json = json.loads(msg_decode)
        msg_string = msg_json["msg"]
        msg_ts = msg_json["ts"]
    except AttributeError:
        try:
            mqtt = MqttRedis.objects.get(member_id=member_id_prefix)
            msg_string = mqtt.message
            msg_ts = int(mqtt.updated_at.timestamp())
        except ObjectDoesNotExist:
            msg_string = ""
            msg_ts = 0

    return msg_string, msg_ts


def get_msg(member_id: str) -> str:
    msg_string, msg_ts = get_msg_redis(member_id)
    return msg_string


def get_msg_ts(member_id: str) -> int:
    msg_string, msg_ts = get_msg_redis(member_id)
    return msg_ts


def get_parameter_by_index(msg: str, index: int = 0) -> str:
    msg_split = msg.split(";")

    try:
        parameter = msg_split[index]
    except IndexError:
        parameter = ""

    return parameter


def get_msg_by_index(member_id: str, index: int = 0) -> str:
    msg = get_msg(member_id)

    return get_parameter_by_index(msg, index)
