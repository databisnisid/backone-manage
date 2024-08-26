from django.db import models
from networks.models import Networks
from django.utils.translation import gettext_lazy as _


class ZabbixNetworks(models.Model):
    name = models.CharField(_('Name'), max_length=50, default='ZabbixNet')
    networks = models.ManyToManyField(Networks)

    created_at = models.DateTimeField(auto_now=False, auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True, auto_now_add=False)


    class Meta:
        db_table = 'zabbix_networks'
        verbose_name = 'Zabbix Network'
        verbose_name_plural = 'Zabbix Networks'

    def __str__(self):
        return '%s' % self.name

    
