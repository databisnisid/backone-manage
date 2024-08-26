from django.db import models
from networks.models import Networks


class ZabbixNetworks(models.Model):
    networks = models.ManyToManyField(Networks)

    created_at = models.DateTimeField(auto_now=False, auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True, auto_now_add=False)


    class Meta:
        db_table = 'zabbix_networks'
        verbose_name = 'Zabbix Network'
        verbose_name_plural = 'Zabbix Networks'

    def __str__(self):
        return '%s' % self.networks

    
