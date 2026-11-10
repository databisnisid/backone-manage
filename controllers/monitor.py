import logging

from django.utils import timezone

from .models import Controllers
from .backend import Zerotier


logger = logging.getLogger(__name__)


def all_controllers_status():
    """
    Refresh cached Controller status. Uses queryset.update() on purpose: the
    model's save() would call the ZeroTier API a second time per controller.
    """
    for controller in Controllers.objects.all():
        zt = Zerotier(controller.uri, controller.token)
        result = zt.status()

        if "online" not in result:
            logger.error(f"Controller {controller.uri} is error!")
            Controllers.objects.filter(pk=controller.pk).update(
                is_online=False, status_checked_at=timezone.now()
            )
            continue

        if not result["online"]:
            logger.warning(f"Controller {controller.uri} is OFFLINE")

        Controllers.objects.filter(pk=controller.pk).update(
            is_online=bool(result["online"]),
            configuration=result,
            status_checked_at=timezone.now(),
        )
