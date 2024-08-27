from django.db import models
from networks.models import Networks
from django.utils.translation import gettext_lazy as _


class ZabbixConfigs(models.Model):
    name = models.CharField(_('Name'), max_length=50)
    url = models.CharField(_('Zabbix API URL'), max_length=200)
    token = models.CharField(_('Zabbix Token'), max_length=200)

    created_at = models.DateTimeField(auto_now=False, auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True, auto_now_add=False)

    class Meta:
        db_table = 'zabbix_configs'
        verbose_name = 'Zabbix Config'
        verbose_name_plural = 'Zabbix Configs'

    def __str__(self):
        return '%s' % self.name


class ZabbixNetworks(models.Model):
    name = models.CharField(_('Name'), max_length=50, default='ZabbixNet')
    networks = models.ManyToManyField(Networks)

    #config = models.ForeignKey(
    config = models.OneToOneField(
            ZabbixConfigs, 
            on_delete=models.SET_NULL,
            verbose_name=_('Zabbix Config'),
            null=True)

    created_at = models.DateTimeField(auto_now=False, auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True, auto_now_add=False)


    class Meta:
        db_table = 'zabbix_networks'
        verbose_name = 'Zabbix Network'
        verbose_name_plural = 'Zabbix Networks'

    def __str__(self):
        return '%s' % self.name

    
