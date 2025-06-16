import redis
import json
from django.conf import settings


def get_msg_redis(member_id: str):
    r = redis.Redis(
        host=settings.MQTT_REDIS_HOST,
        port=settings.MQTT_REDIS_PORT,
        db=settings.MQTT_REDIS_DB,
    )
    msg = r.get(str(f"{settings.MQTT_REDIS_PREFIX}:{member_id}"))
    try:
        msg_decode = msg.decode()
        msg_json = json.loads(msg_decode)
        msg_string = msg_json["msg"]
        msg_ts = msg_json["ts"]
    except AttributeError:
        msg_string = ""
        msg_ts = 0

    return msg_string, msg_ts


def get_msg(member_id: str) -> str:
    msg_string, msg_ts = get_msg_redis(member_id)
    return msg_string


def get_msg_ts(member_id: str) -> int:
    msg_string, msg_ts = get_msg_redis(member_id)
    return msg_ts


def get_msg_by_index(member_id: str, index: int = 0) -> str:
    msg = get_msg(member_id)
    msg_split = msg.split(";")

    try:
        parameter = msg_split[index]
    except IndexError:
        parameter = ""

    return parameter
