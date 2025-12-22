import re
import logging
import sys
from django.conf import settings
from django.http import HttpResponse
from django.template.loader import render_to_string
from django.test.testcases import template_rendered
from config.utils import check_device_id

logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)


class CorsMiddleware(object):
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        response["Access-Control-Allow-Origin"] = "*"
        return response


class CheckHeadersMiddleware(object):
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        logger = logging.getLogger(
            name="CheckHeaderMiddleware" + __name__ + ".__call__"
        )
        logger.debug(request.headers)
        if settings.IS_CUSTOM_USER_AGENT:
            logger.debug(request.headers)
            user_agent = request.headers["User-Agent"]
            try:
                device_id = request.headers["Device-Id"]
            except KeyError:
                device_id = ""

            is_superagent = False
            if settings.SUPER_USER_AGENT:
                is_user_agent_super = re.search(
                    rf"{settings.SUPER_USER_AGENT}", user_agent
                )
                if is_user_agent_super:
                    is_superagent = True

            if not is_superagent:
                is_user_agent = re.search(rf"{settings.CLIENT_USER_AGENT}", user_agent)
                logger.debug(settings.CLIENT_USER_AGENT)
                logger.debug(is_user_agent)
                if not is_user_agent:
                    template_rendered = render_to_string(
                        "dashboard/update-client.html", {}
                    )
                    return HttpResponse(template_rendered)
                else:
                    is_device_authorized = check_device_id(device_id)
                    # logger.debug(f"{device_id} is {is_device_authorized}")
                    if not is_device_authorized:
                        template_rendered = render_to_string(
                            "dashboard/device-not-authorized.html",
                            {"device_id": device_id},
                        )
                        return HttpResponse(template_rendered)

        response = self.get_response(request)
        return response
