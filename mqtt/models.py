from django.db import models
from django.utils.translation import gettext as _
from django.core.exceptions import ObjectDoesNotExist


class Mqtt(models.Model):
    member_id = models.CharField(_('Member ID'), max_length=50)
    model = models.CharField(_('Model'), max_length=50, blank=True, null=True)
    board_name = models.CharField(_('Board Name'), max_length=50, blank=True, null=True)
    release_version = models.CharField(_('Release Version'), max_length=50, blank=True, null=True)
    release_target = models.CharField(_('Release Target'), max_length=50, blank=True, null=True)

    ipaddress = models.GenericIPAddressField(_('IP Address'), blank=True, null=True)

    is_rcall = models.BooleanField(_('RCALL Running'), default=False)
    uptime = models.CharField(_('Uptime'), max_length=100, blank=True, null=True)
    serialnumber = models.CharField(_('SN'), max_length=100, blank=True, null=True)
    num_core = models.IntegerField(_('Number of Core'), default=1)
    cpu_usage = models.FloatField(_('CPU Usage'), default=0.0)
    memory_usage = models.FloatField(_('Memory Usage'), default=0.0)
    packet_loss_string = models.CharField(_('Packet Loss String'),  max_length=100, blank=True, null=True)
    round_trip_string = models.CharField(_('Round Trip String'),  max_length=100, blank=True, null=True)
    packet_loss = models.FloatField(_('Packet Lost'), default=0)
    round_trip = models.FloatField(_('Round Trip'), default=0)

    class Meta:
        db_table = 'mqtt'
        verbose_name = 'MQTT'
        verbose_name_plural = 'MQTT'

    created_at = models.DateTimeField(auto_now=False, auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True, auto_now_add=False)

    def __str__(self):
        return '{}'.format(self.member_id)

    def save(self):
        if self.packet_loss_string:
            packet_loss_split = self.packet_loss_string.split(',')
            packet_lost_digit_string = packet_loss_split[2].split('%')
            self.packet_loss = float(packet_lost_digit_string[0])

        if self.round_trip_string:
            round_trip_string = self.round_trip_string.split('=')
            round_trip_digit = round_trip_string[1].split('/')
            self.round_trip = float(round_trip_digit[1])

        if self.uptime:
            load_string = self.uptime.split('load average:')
            load_digit = load_string[1].split(',')
            self.cpu_usage = float(load_digit[1]) / self.num_core * 100

        return super(Mqtt, self).save()

