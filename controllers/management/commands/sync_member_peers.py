from time import sleep
import redis
import logging
from django.utils import timezone
from redis.exceptions import TimeoutError, ConnectionError
import json
from controllers.backend import Zerotier
from django.core.management.base import BaseCommand
from django.conf import settings
from members.models import Members, MemberPeers


logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Daemon to syncronize Member Peers to Redis"

    def handle(self, *args, **options):

        r = redis.Redis(
            host=settings.MQTT_REDIS_HOST,
            port=settings.MQTT_REDIS_PORT,
            db=int(settings.MQTT_REDIS_DB + 1),
            socket_timeout=1,
        )

        # Re-read per loop: a cached queryset misses members created after the
        # daemon started, which is how a new node stays permanently "offline".
        """ Loop Forever """
        while True:
            members = (
                Members.objects.filter(is_authorized=True)
                .select_related("network__controller")
            )
            # current_time = timezone.now()
            # timestamp = int(current_time.timestamp())
            # for member_peer in member_peers:
            logger.info(f"Start - Syncronize")
            for member in members:
                # One bad member (deleted network, dead controller) must not
                # stop the daemon and leave every other member stale.
                try:
                    zt = Zerotier(
                        member.network.controller.uri,
                        member.network.controller.token,
                    )
                    peers = zt.get_member_peers(member.member_id)
                    r.setex(
                        f"{settings.MQTT_REDIS_PREFIX}:{member.member_id}",
                        settings.MQTT_REDIS_SETEX,
                        json.dumps({"peers": peers}),
                    )
                except (TimeoutError, ConnectionError):
                    pass
                except Exception as e:
                    logger.warning(f"sync_member_peers {member.member_id}: {e}")

            logger.info(
                f"End - Syncronize. Sleep for {settings.SYNC_MEMBER_PEERS_SLEEP} seconds"
            )
            """ Sleep for x seconds """
            sleep(settings.SYNC_MEMBER_PEERS_SLEEP)
