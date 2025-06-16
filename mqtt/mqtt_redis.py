import redis
from django.conf import settings


def get_msg(member_id: str) -> str:
    r = redis.Redis(
        host=settings.MQTT_REDIS_HOST,
        port=settings.MQTT_REDIS_PORT,
        db=settings.MQTT_REDIS_DB,
    )
    msg = r.get(str(member_id))
    try:
        msg_decode = msg.decode()
    except AttributeError:
        msg_decode = ""

    return msg_decode


def get_msg_by_index(member_id: str, index: int = 0) -> str:
    msg = get_msg(member_id)
    msg_split = msg.split(";")

    try:
        parameter = msg_split[index]
    except IndexError:
        parameter = ""

    return parameter
