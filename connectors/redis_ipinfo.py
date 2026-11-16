from django.core.exceptions import ObjectDoesNotExist
import redis
from redis.exceptions import TimeoutError
import json
from django.conf import settings
from config.utils import convert_python_booleans_to_json


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
            msg_string_clean = convert_python_booleans_to_json(msg_string)
            # print(f"redis_ipinfo -> {msg_string}")
            # print(f"redis_ipinfo -> {msg_string_clean}")

            try:
                msg_json = json.loads(msg_string_clean)
            except json.JSONDecodeError as e:
                msg_json = {}

            try:
                result = msg_json["as_name"]
            except KeyError:
                pass

        except AttributeError:
            pass

    return result

def get_ip_loc(ipaddress: str):
    """Return (lat, lng) from IPInfo Redis cache, or None if no geo data."""
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
            msg_string_clean = convert_python_booleans_to_json(msg_string)
            msg_json = json.loads(msg_string_clean)
            loc = msg_json.get("loc", "")
            if loc and "," in loc:
                lat_str, lng_str = loc.split(",", 1)
                return float(lat_str), float(lng_str)
        except (json.JSONDecodeError, ValueError, AttributeError):
            pass

    return None
