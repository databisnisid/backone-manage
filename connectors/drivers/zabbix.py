from django.db.models import NullBooleanField
from zabbix_utils import ZabbixAPI
from django.conf import settings

"""
Create:
zapi.api.host.create(host="test-zabbix",name="Test Zabbix",interfaces=[],groups=[{"groupid": 29}])

Search Group:
zapi.api.hostgroup.get(search={'name': 'Nexus'}, output=['name', 'groupid'])
"""


class Zabbix:
    def __init__(self, zabbix_url=None, zabbix_token=None):

        if zabbix_url:
            self.url = zabbix_url
        else:
            self.url = settings.ZABBIX_URL

        if zabbix_token:
            self.token = zabbix_token
        else:
            self.token = settings.ZABBIX_TOKEN

        self.api = ZabbixAPI(url=self.url)
        # self.api = ZabbixAPI(url=self.url, skip_version_check=True)
        self.api.login(token=self.token)
        self.hosts = []

    def host_get(self, output=["hostid", "host"]):
        self.hosts = self.api.host.get(output)
        return self.hosts

    def host_get_hostid(self, hostname="Zabbix server"):
        if not self.hosts:
            self.host_get()

        result = None
        for host in self.hosts:
            if host["host"] == hostname:
                result = host["hostid"]
                break

        return result

    def hostgroup_get_groupid(self, groupname: str = "Zabbix servers") -> int:
        """
        zapi.api.hostgroup.get(search={"name": "Nexus"}, output=["name", "groupid"])
        """
        search = {"name": groupname}
        output = ["name", "groupid"]
        result = self.api.hostgroup.get(search=search, output=output)

        if result:
            result = result[0]["groupid"]

        return result

    def host_update(self, hostname="Zabbix server"):
        pass

    def host_update_inventory(self, hostname="Zabbix server", params={}):
        hostid = self.host_get_hostid(hostname)

        result = None
        if hostid:
            # print(hostid)
            params = {"hostid": hostid} | params
            result = self.api.host.update(params)

        return result

    def host_create(self):
        pass

    """ Not Working """
    """
    def host_create(self, hostname="Zabbix server", params={}):
        result = self.api.host.create(host=hostname, params)
        return result
    """

    def host_search(self):
        pass

    def host_search_by_severity(self):
        pass
