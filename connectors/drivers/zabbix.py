from django.db.models import NullBooleanField
from zabbix_utils import ZabbixAPI
from django.conf import settings



class Zabbix:
    def __init__(self):
        self.url = settings.ZABBIX_URL
        self.token = settings.ZABBIX_TOKEN
        self.api = ZabbixAPI(url=self.url)
        self.api.login(token=self.token)
        self.hosts = []

    def host_get(self, output=['hostid', 'host']):
        self.hosts = self.api.host.get(output)
        return self.hosts

    def host_get_hostid(self, hostname="Zabbix server"):
        if not self.hosts:
            self.host_get()

        result = None
        for host in self.hosts:
            if host['host'] == hostname:
                result = host['hostid']
                break

        return result

    def host_update(self, hostname="Zabbix server"):
        pass

    def host_update_inventory(self, hostname="Zabbix server"):
        hostid = self.host_get_hostid(hostname)

        result = None
        if hostid:
            print(hostid)
            #self.api.login(token=self.token)
            params = {
                    "hostid": hostid,
                    "inventory_mode": 1,
                    "inventory": {
                        "location": "Jakarta"
                        }
                    }
            result = self.api.host.update(
                    params
                    #hostid=hostid,
                    #inventory_mode=1,
                    #inventory='{"location": "Indonesia"}'
                    )

        return result

    def host_create(self):
        pass

    def host_search(self):
        pass

    def host_search_by_severity(self):
        pass
