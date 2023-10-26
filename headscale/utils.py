from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from connectors.drivers.headscale import Headscale
#from config.utils import to_list


def add_user(hs_user):
    hs = Headscale(settings.HEADSCALE_URI, settings.HEADSCALE_KEY)
    result = hs.add_user(hs_user)

    try:
        result['user']
        is_ok = True

    except KeyError:
        is_ok = False

    return is_ok, result['user']

def rename_user(hs_user, hs_user_new):
    hs = Headscale(settings.HEADSCALE_URI, settings.HEADSCALE_KEY)
    result = hs.rename_user(hs_user, hs_user_new)

    try:
        result['user']
        is_ok = True

    except KeyError:
        is_ok = False

    return is_ok, result['user']


def delete_user(hs_user):
    hs = Headscale(settings.HEADSCALE_URI, settings.HEADSCALE_KEY)
    result = hs.delete_user(hs_user)

    is_ok = False
    if result == '{}':
        is_ok = True

    return is_ok


def add_preauth_key(hs_user):
    hs = Headscale(settings.HEADSCALE_URI, settings.HEADSCALE_KEY)
    result = hs.add_preauth_key(hs_user)

    try:
        result['preAuthKey']
        is_ok = True

    except KeyError:
        is_ok = False

    return is_ok, result['preAuthKey']

