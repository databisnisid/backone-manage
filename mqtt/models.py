import re
from django.db import models
from django.conf import settings
from django.utils import timezone
from config.utils import get_uptime_string, get_cpu_usage
from django.utils.translation import gettext as _
from django.core.exceptions import ObjectDoesNotExist
from wagtail import permissions


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
    switchport_up = models.CharField(_('Switch Port Up'), max_length=20, blank=True, null=True)
    port_status = models.CharField(_('Port Status'), max_length=200, blank=True, null=True)
    quota_vnstat = models.CharField(_('Quota VNStat'), max_length=200, blank=True, null=True)
    quota_first = models.CharField(_('Quota'), max_length=200, blank=True, null=True)

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
            packet_loss_digit_string = packet_loss_split[2].split('%')

            try:
                self.packet_loss = float(packet_loss_digit_string[0])
            except ValueError:
                self.packet_loss = 0

        if self.round_trip_string:
            round_trip_string = self.round_trip_string.split('=')
            round_trip_digit = round_trip_string[1].split('/')

            try:
                self.round_trip = float(round_trip_digit[1])
            except ValueError:
                self.round_trip = 0

        if self.uptime:
            load_1, load_5, load_15 = get_cpu_usage(self.uptime, self.num_core)
            #load_string = self.uptime.split('load average:')
            #load_digit = load_string[1].split(',')

            try:
                #self.cpu_usage = float(load_digit[1]) / self.num_core * 100
                self.cpu_usage = load_5
            except ValueError:
                self.cpu_usage = 0

        return super(Mqtt, self).save()


    def get_quota_first(self):
        quota_current = 0
        quota_total = 0
        quota_day = 0

        if self.quota_first:
            quota_split = self.quota_first.split('/')
            try:
                quota_split[0]
                quota_current = float(re.sub("[^0-9].", "", quota_split[0]))
            except (ValueError, IndexError) as error:
                quota_current = 0

            try:
                quota_split[1]
                quota_total = float(re.sub("[^0-9].", "", quota_split[1]))
            except (ValueError, IndexError) as error:
                quota_current = 0
                quota_total = 0 

            try:
                quota_split[2]
                quota_day = float(re.sub("[^0-9].", "", quota_split[2]))
            except (ValueError, IndexError) as error:
                quota_current = 0
                quota_total = 0 
                quota_day = 0

        return quota_current, quota_total, quota_day

    def get_quota_vnstat(self):
        rx_usage = 0
        tx_usage = 0
        total_usage = 0
        split_text = []
    
        if self.quota_vnstat:
            split_text = self.quota_vnstat.split(',')

            ''' RX Usage '''
            try:
                rx_usage = int(split_text[2])
            except (IndexError, ValueError) as error:
                pass

            ''' TX Usage '''
            try:
                tx_usage = int(split_text[3])
            except (IndexError, ValueError) as error:
                pass

            ''' Total Usage '''
            try:
                total_usage = int(split_text[4])
            except (IndexError, ValueError) as error:
                pass

        return rx_usage, tx_usage, total_usage


    ''' This is to get all 1min, 5 min, 15min load '''
    def get_cpu_usage(self):
        if self.uptime:
            load_1, load_5, load_15 = get_cpu_usage(self.uptime, self.num_core)
        else:
            load_1 = load_5 = load_15 = 0.0

        return round(load_1, 1), round(load_5, 1), round(load_15, 1)


    def get_uptime_string(self):
        uptime_string = ''
        if self.uptime:
            uptime_load = get_uptime_string(self.uptime)
            uptime_split = uptime_load.split('load average')
            uptime_string = uptime_split[0][:-3:]

        return uptime_string.strip()

    def get_packet_loss(self):
        packet_loss = 0

        if self.packet_loss_string:
            packet_loss_split = self.packet_loss_string.split(',')
            packet_loss_digit_string = packet_loss_split[2].split('%')

            try:
                packet_loss = float(packet_loss_digit_string[0])
            except ValueError:
                packet_loss = 0

        return packet_loss

    def get_round_trip(self):
        round_trip = 0

        if self.round_trip_string:
            round_trip_string = self.round_trip_string.split('=')
            round_trip_digit = round_trip_string[1].split('/')

            try:
                round_trip = float(round_trip_digit[1])
            except ValueError:
                round_trip = 0

        return round_trip

    def is_online(self):
        online_status = False
        now = timezone.now()
        delta = now - timezone.localtime(self.updated_at)
        if delta.seconds < settings.ONLINE_STATUS_DELAY:
            online_status = True

        return online_status

