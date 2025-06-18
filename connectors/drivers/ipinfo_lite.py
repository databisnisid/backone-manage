import requests
from requests.exceptions import ConnectionError
from django.conf import settings


IPINFO_LITE_URI = "https://api.ipinfo.io/lite/"


def lookup_ipaddress(ipaddress: str = "8.8.8.8") -> dict:
    try:
        request_uri = f"{IPINFO_LITE_URI}{ipaddress}?token={settings.IPINFO_LITE_TOKEN}"
        response = requests.get(request_uri)
        return response.json()

    except ConnectionError:
        return {}
