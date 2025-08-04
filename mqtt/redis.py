from django.core.exceptions import ObjectDoesNotExist
import redis
from redis.exceptions import TimeoutError
import json
from django.conf import settings
from .models import Mqtt


def get_msg_redis(member_id: str):
    """
    r = redis.Redis(
        host=settings.MQTT_REDIS_HOST,
        port=settings.MQTT_REDIS_PORT,
        db=settings.MQTT_REDIS_DB,
        socket_timeout=1,
    )
    """
    member_id_prefix = f"{settings.MQTT_REDIS_PREFIX}:{member_id}"
    # msg = r.get(str(f"{settings.MQTT_REDIS_PREFIX}:{member_id}"))
    msg_string = ""
    msg_ts = 0

    try:
        msg = settings.MQTT_REDIS_CONN.get(member_id_prefix)
        # msg = r.get(member_id_prefix)

    except TimeoutError:
        msg = None

    try:
        msg_decode = msg.decode()
        msg_json = json.loads(msg_decode)
        msg_string = msg_json["msg"]
        msg_ts = msg_json["ts"]

    except AttributeError:
        """If not respond from REDIS, try to get from DB"""
        try:
            # mqtt = MqttRedis.objects.get(member_id=member_id_prefix)
            mqtt = Mqtt.objects.get(member_id=member_id)
            msg_string = mqtt.message
            msg_ts = int(mqtt.updated_at.timestamp())
        except ObjectDoesNotExist:
            pass

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
