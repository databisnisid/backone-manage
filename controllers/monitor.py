import logging
from .models import Controllers
from .backend import Zerotier


logger = logging.getLogger(__name__)


def all_controllers_status():
    controllers = Controllers.objects.all()

    for controller in controllers:
        zt = Zerotier(controller.uri, controller.token)
        result = zt.status()

        is_online = False
        try:
            is_online = result["online"]
            is_error = False
        except KeyError:
            is_error = True

        if is_error:
            logger.error(f"Controller {controller.uri} is error!")
        elif not is_online:
            logger.warning(f"Controller {controller.uri} is OFFLINE")
        else:
            pass
