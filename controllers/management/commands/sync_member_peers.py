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
            db=settings.MQTT_REDIS_DB,
            socket_timeout=1,
        )

        # member_peers = MemberPeers.objects.all()
        members = Members.objects.filter(is_authorized=True)

        """ Loop Forever """
        while True:
            # current_time = timezone.now()
            # timestamp = int(current_time.timestamp())
            # for member_peer in member_peers:
            logger.info(f"Start - Syncronize")
            for member in members:
                zt = Zerotier(
                    member.network.controller.uri,
                    member.network.controller.token,
                    # member_peer.network.controller.token,
                    # member_peer.network.controller.uri,
                )
                # peers = zt.get_member_peers(member_peer.member_id)
                peers = zt.get_member_peers(member.member_id)
                logger.info(f"{peers}")
                member_id_with_prefix = (
                    f"{settings.MQTT_REDIS_PREFIX}:{member.member_id}"
                )
                msg_json = {}
                msg_json["peers"] = peers
                # msg_json["ts"] = timestamp
                msg_json_string = str(msg_json).replace("'", '"')

                try:
                    r.setex(
                        member_id_with_prefix,
                        settings.MQTT_REDIS_SETEX,
                        msg_json_string,
                    )
                except TimeoutError or ConnectionError:
                    pass

            logger.info(
                f"End - Syncronize. Sleep for {settings.SYNC_MEMBER_PEERS_SLEEP} seconds"
            )
            """ Sleep for x seconds """
            sleep(settings.SYNC_MEMBER_PEERS_SLEEP)
