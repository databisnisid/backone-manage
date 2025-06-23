from django.core.exceptions import ObjectDoesNotExist
import redis
from redis.exceptions import TimeoutError
import json
from django.conf import settings


def get_as_name(ipaddress: str) -> str:
    result = ""
    r = redis.Redis(
        host=settings.MQTT_REDIS_HOST,
        port=settings.MQTT_REDIS_PORT,
        db=settings.MQTT_REDIS_DB,
        socket_timeout=1,
    )
    key = f"{settings.IPINFO_LITE_PREFIX}:{ipaddress}"
    try:
        msg = r.get(key)
    except TimeoutError:
        msg = None

    if msg:
        try:
            msg_string = msg.decode()
            msg_json = json.loads(msg_string)
            try:
                result = msg_json["as_name"]
            except KeyError:
                pass

        except AttributeError:
            pass

    return result
