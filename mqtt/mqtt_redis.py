import redis
from django.conf import settings


def get_msg() -> str:
    r = redis.Redis(host=settings.MQTT_REDIS_HOST)
    msg = r.get(str(self.member_id))
    try:
        msg_decode = msg.decode()
    except AttributeError:
        msg_decode = ""

    return msg_decode


def get_msg_by_index(index: int = 0) -> str:
    msg = get_msg()
    msg_split = msg.split(";")

    try:
        parameter = msg_split[index]
    except IndexError:
        parameter = ""

    return parameter
