from django.db import models
from django.utils.translation import gettext as _


class Mqtt(models.Model):
    member_id = models.CharField(_('Member ID'), max_length=50)
    model = models.CharField(_('Model'), max_length=50, blank=True, null=True)
    board_name = models.CharField(_('Board Name'), max_length=50, blank=True, null=True)
    release_version = models.CharField(_('Release Version'), max_length=50, blank=True, null=True)
    release_target = models.CharField(_('Release Target'), max_length=50, blank=True, null=True)

    ipaddress = models.GenericIPAddressField(_('IP Address'), blank=True, null=True)

    class Meta:
        db_table = 'mqtt'
        verbose_name = 'MQTT'
        verbose_name_plural = 'MQTT'

    created_at = models.DateTimeField(auto_now=False, auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True, auto_now_add=False)

    def __str__(self):
        return '{}'.format(self.member_id)
