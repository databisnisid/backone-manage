from django.db.models import NullBooleanField
from zabbix_utils import ZabbixAPI
from django.conf import settings



class Zabbix:
    def __init__():
        url = settings.ZABBIX_URL
        token = settings.ZABBIX_TOKEN
        api = ZabbixAPI(url=url)
        api.login(token=token)

    def get_host():
        pass

    def create_host():
        pass

    def search_host():
        pass

    def search_host_by_severity():
        pass
