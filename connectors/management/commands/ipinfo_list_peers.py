import redis
from redis.exceptions import TimeoutError
import json
from connectors.drivers.ipinfo_lite import lookup_ipaddress
from django.core.management.base import BaseCommand
from django.conf import settings
from members.models import Members


class Command(BaseCommand):
    help = "Daemon to resolve IP from ipinfo API to Redis"

    def handle(self, *args, **options):

        r = redis.Redis(
            host=settings.MQTT_REDIS_HOST,
            port=settings.MQTT_REDIS_PORT,
            db=settings.MQTT_REDIS_DB,
            socket_timeout=1,
        )

        members = Members.objects.all()

        for member in members:
            list_peers = member.list_ip_peers()

            if list_peers:
                for list_peer in list_peers:
                    msg = lookup_ipaddress(list_peer)
                    try:
                        r.set(
                            f"{settings.IPINFO_LITE_PREFIX}:{list_peer}",
                            str(msg).replace("'", '"'),
                        )
                    except TimeoutError:
                        pass
