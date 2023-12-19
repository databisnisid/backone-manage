import re
from datetime import datetime
from os import walk
from crum import get_current_user
from django.db import models
from django.utils import timezone
from django.conf import settings
from accounts.models import User, Organizations
from networks.models import Networks, NetworkRoutes
from monitor.utils import check_members_vs_rules
from monitor.models import MonitorRules
from django.utils.translation import gettext as _
from django.utils.html import format_html
from controllers.backend import Zerotier
from django.core.validators import RegexValidator
from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned
from config.utils import to_dictionary, readable_timedelta, calculate_bandwidth_unit
from ipaddress import ip_address, ip_network
from django.core.exceptions import ValidationError
from mqtt.models import Mqtt


'''
MemberPeers Model
'''
class MemberPeers(models.Model):
    peers = models.TextField(_('Peers'))
    member_id = models.CharField(_('Member ID'), max_length=50)
    network = models.ForeignKey(
        Networks,
        on_delete=models.CASCADE,
        verbose_name=_('Network'),
    )

    created_at = models.DateTimeField(auto_now=False, auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True, auto_now_add=False)

    class Meta:
        db_table = 'member_peers'
        verbose_name = 'member peer'
        verbose_name_plural = 'member peers'

    def __str__(self):
        return '%s' % self.peers

    def save(self):
        zt = Zerotier(self.network.controller.uri, self.network.controller.token)
        self.peers = zt.get_member_peers(self.member_id)
        return super(MemberPeers, self).save()


class Members(models.Model):
    def limit_choices_to_current_user():
        user = get_current_user()
        if not user.is_superuser:
            if user.organization.is_no_org:
                return {'user': user}
            else:
                return {'organization': user.organization}
        else:
            return {}

    name = models.CharField(_('Member Name'), max_length=50)
    member_code = models.CharField(_('Member Code'), max_length=20, blank=True, null=True)
    description = models.TextField(_('Description'), blank=True)
    member_id = models.CharField(_('Member ID'), max_length=50)
    network = models.ForeignKey(
        Networks,
        on_delete=models.CASCADE,
        limit_choices_to=limit_choices_to_current_user,
        verbose_name=_('Network'),
    )
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        verbose_name=_('Owner'),
        null=True
    )
    organization = models.ForeignKey(
        Organizations,
        on_delete=models.SET_NULL,
        verbose_name=_('Organization'),
        null=True
    )

    is_bridge = models.BooleanField(_('Bridge Mode'), default=False)
    is_no_auto_ip = models.BooleanField(_('No Auto Assign IP'), default=False)
    is_authorized = models.BooleanField(_('Authorized'), default=True)
    tags = models.CharField(_('Tags'), max_length=50, blank=True, null=True,
                            help_text=_('Example: ssh_client'))
    ipaddress = models.CharField(_('IP Address'), max_length=100, blank=True, null=True)
    #serialnumber = models.CharField(_('SN'), max_length=100, blank=True, null=True)
    address = models.CharField(max_length=250, blank=True, null=True)
    location = models.CharField(max_length=250, blank=True, null=True)
    online_at = models.DateField(_('Start Online'), blank=True, null=True)
    offline_at = models.DateTimeField(_('Stop Online'), blank=True, null=True)

    # WAF
    is_waf = models.BooleanField(_('WebFilter Active'), default=False)

    # Mobile
    mobile_regex = RegexValidator(regex=r'^62\d{9,15}$', message=_("Mobile number must be entered in the format: '628XXXXXXXXXXX'. Up to 15 digits allowed."))
    mobile_number_first = models.CharField(_('Mobile Number'), 
                                     validators=[mobile_regex], 
                                     max_length=20, blank=True, null=True)


    configuration = models.TextField(_('Configuration'), blank=True)

    peers = models.ForeignKey(
        MemberPeers,
        on_delete=models.SET_NULL,
        verbose_name=_('Peers'),
        null=True
    )

    mqtt = models.ForeignKey(
        Mqtt,
        on_delete=models.SET_NULL,
        verbose_name=_('Mqtt'),
        null=True
    )

    created_at = models.DateTimeField(auto_now=False, auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True, auto_now_add=False)

    class Meta:
        db_table = 'members'
        verbose_name = 'member'
        verbose_name_plural = 'members'

    def __str__(self):
        return '%s' % self.name

    def delete(self, using=None, keep_parents=False):
        zt = Zerotier(self.network.controller.uri, self.network.controller.token)
        zt.delete_member(self.network.network_id, self.member_id)
        return super(Members, self).delete()

    def save(self):
        self.user = self.network.user
        self.organization = self.network.organization
        if self.member_code:
            self.member_code = self.member_code.upper()

        # Zerotier
        zt = Zerotier(self.network.controller.uri, self.network.controller.token)

        # Authorized and Bridge Setting
        data = {'authorized': self.is_authorized,
                'activeBridge': self.is_bridge,
                'noAutoAssignIps': self.is_no_auto_ip}

        # Assign IP Address
        if self.ipaddress is not None:
            self.ipaddress = self.ipaddress.replace(' ', '')
            ip_address_lists = self.ipaddress.split(',')
            data['ipAssignments'] = ip_address_lists

        # Apply Configuration to controller
        print('Member', self.member_id, data)
        member_info = zt.set_member(self.network.network_id, self.member_id, data)
        self.configuration = member_info

        # Get MemberPeers
        try:
            member_peers = MemberPeers.objects.get(member_id=self.member_id)
        except ObjectDoesNotExist:
            member_peers = MemberPeers(member_id=self.member_id)
        except MultipleObjectsReturned:
            #member_peers = MemberPeers.objects.filter(member_id=self.member_id).first()
            member_peers = MemberPeers.objects.filter(member_id=self.member_id).delete()
            member_peers = MemberPeers(member_id=self.member_id)
        member_peers.peers = zt.get_member_peers(self.member_id)
        member_peers.network = self.network
        member_peers.save()
        self.peers = member_peers

        if self.mqtt is None:
            try:
                mqtt = Mqtt.objects.get(member_id=self.member_id)
                self.mqtt = mqtt
            except ObjectDoesNotExist:
                pass

        return super(Members, self).save()

    def clean(self):
        try:
            self.network.network_id
        except ObjectDoesNotExist:
            raise ValidationError({'network': _('Please choose Network')})

        #if self.network is None:
        #    raise ValidationError({'Network': _('Please choose Network')})

        # Check mobile_number_first is not Unique
        if self.mobile_number_first is not None:
            try:
                Members.objects.exclude(
                        id=self.id
                        ).get(mobile_number_first=self.mobile_number_first)
                raise ValidationError({'mobile_number_first': _('Mobile Number is already used!')})
            except ObjectDoesNotExist:
                pass

        # Check if member_id is already in this network

        if self.member_id:
            if self.id is None:
                try:
                    Members.objects.get(member_id=self.member_id, network=self.network)
                    raise ValidationError({'member_id': _('Member ID already exist in this network!')})
                except ObjectDoesNotExist:
                    pass
            if len(self.member_id) != 10:
                raise ValidationError({'member_id': _('Member ID must be 10 characters!')})

        # CHECK: For multiple IP in self.ipaddress
        # Check for list IP_address
        if self.ipaddress is not None:
            self.ipaddress = self.ipaddress.replace(' ', '')
            ip_address_lists = self.ipaddress.split(',')

            for ip_address_list in ip_address_lists:
                try:
                    ip_address(ip_address_list)
                except ValueError:
                    raise ValidationError({'ipaddress': _('Wrong Format')})

        # New Block Validation compare to ip_network
            if self.network.ip_address_networks is not None:
                ip_network_lists = self.network.ip_address_networks.split(',')

                #is_ipaddress_in_network = False
                ip_status = {}
                for ip_address_list in ip_address_lists:
                    ip_status[ip_address_list] = False
                    print(ip_address_list)
                    for ip_network_list in ip_network_lists:
                        print(ip_network_list)
                        if ip_address(ip_address_list) in ip_network(ip_network_list):
                            is_ipaddress_in_network = True
                            ip_status[ip_address_list] = True
                            break
                        #else:
                            #is_ipaddress_in_network = False
                #print(ip_status)
                #if not is_ipaddress_in_network:
                for ip_address_list in ip_address_lists:
                    if not ip_status[ip_address_list]:
                        raise ValidationError({'ipaddress': _('IP address should be in segment ' +
                                                              self.network.ip_address_networks)})

                # Second Raise
                for ip_address_list in ip_address_lists:

                    members = Members.objects.filter(
                        ipaddress__contains=ip_address_list).exclude(member_id=self.member_id)

                    if members:
                        is_duplicate = False
                        for member in members:
                            if ',' in member.ipaddress:
                                m_ipaddress = member.ipaddress.split(',')
                                for m_ip in m_ipaddress:
                                    if m_ip == ip_address_list:
                                        is_duplicate = True
                            elif member.ipaddress == ip_address_list:
                                is_duplicate = True
                        if is_duplicate:
                            raise ValidationError(
                                {'ipaddress': _('IP address ' + ip_address_list + ' is already used!')})
            else:
                raise ValidationError(_('First, please setup IP Network in ' + self.network.name))

    def list_ipaddress(self):
        text = ''
        if self.ipaddress is not None:
            ipaddress_list = self.ipaddress.split(',')
            text = format_html('<br />'.join([str(p) for p in ipaddress_list]))

        is_authorized = "icon-yes.svg" if self.is_authorized else "icon-no.svg"
        #return text

        if self.mobile_number_first is not None:
            text += format_html('<br />{}', self.mobile_number_first)

        return format_html('<small>'
                           + '<strong>{}</strong>'
                           + " <img src='/static/admin/img/{}'>"
                           + '<br />{}'
                           + '<br />{}</small>',
                           self.member_id, is_authorized, text, self.network.name
                           )
    list_ipaddress.short_description = _('ID, IP and Network')

    def list_peers(self):
        peers = to_dictionary('{}')
        if self.peers:
            peers = to_dictionary(self.peers.peers)
        if 'paths' in peers and len(peers['paths']) != 0:
            paths = peers['paths']
            ip_peers = []
            ip_peers_html = []
            for path in paths:
                ip_path = path['address'].split('/')
                if ip_path[0] not in ip_peers:
                    ip_info = "<a href='https://ipinfo.io/{}' target='_blank' rel='noopener noreferrer'>{}</a>".format(ip_path[0], ip_path[0])
                    ip_peers.append(ip_path[0])
                    ip_peers_html.append(ip_info)

            result = '<br />'.join([str(p) for p in ip_peers_html])
            return format_html('<small>' + result + '</small>')
        else:
            return ''

    list_peers.short_description = _('Peers          ')

    def member_status(self):
        peers = to_dictionary('{}')
        if self.peers:
            peers = to_dictionary(self.peers.peers)

        if 'paths' in peers and len(peers['paths']) != 0:
            version = peers['version']
            latency = peers['latency']

            if latency < 0:
                direct_or_relay = 'RELAY'
                text = format_html("<small>{} ({})</small>",
                                    direct_or_relay, version)
            else:
                direct_or_relay = 'DIRECT'
                text = format_html("<small>{} ({}/{}ms)</small>",
                                    direct_or_relay, version, str(latency))

            #text = format_html("<small style='color: green;'>ONLINE ({})<br />{}({}ms)<br />{}</small>",
            #                   version, peers['role'], str(latency), direct_or_relay)
            #text = format_html("<small style='color: green;'>{} ({}/{}ms)</small>",
            #                   direct_or_relay, version, str(latency))
        else:
            controller_configuration = to_dictionary(self.network.controller.configuration)
            if self.peers:
                peers = to_dictionary(self.peers.peers)

            if self.member_id == controller_configuration['address']:
                version = controller_configuration['version']
                text = format_html("<small style='color: blue;'>CONTROLLER ({})</small>", version)
            elif self.peers:
                if 'role' in self.peers.peers and 'latency' in self.peers.peers \
                    and 'version' in self.peers.peers: # and int(self.peers.peers['latency']) == -1:
                    text = format_html("<small>RELAY ({})</small>", peers['version'])
                else:
                    text = format_html("<small style='color: red;'>OFFLINE</small>")
            else:
                text = format_html("<small style='color: red;'>OFFLINE</small>")

        #return text
        ipaddress_ts = self.ipaddress_ts()
        if ipaddress_ts:
            text =  format_html(self.list_ipaddress() + '<br />' + text + '<br /><small>IP TS: ' + ipaddress_ts + '</small>')
        else:
            text = format_html(self.list_ipaddress() + '<br />' + text)

        if self.is_waf:
            return format_html(text + '<br /><small>WAF: On</small>')
        else:
            return format_html(text + '<br /><small>WAF: Off</small>')


    member_status.short_description = _('Member Status')

    def is_online(self):
        online_status = False
        peers = to_dictionary('{}')
        #if self.peers:
        try:
            self.peers
            try:
                peers = to_dictionary(self.peers.peers)
                if 'paths' in peers and len(peers['paths']) != 0 and self.ipaddress:
                    online_status = True
                if 'role' in self.peers.peers and 'latency' in self.peers.peers \
                    and 'version' in self.peers.peers: # and int(self.peers.peers['latency']) == -1:
                    online_status = True
            except AttributeError:
                pass
        except KeyError:
            pass

        return online_status
    is_online.short_description = _('BackOne Online')

    def online_status(self):
        text = 'OFFLINE'
        color = 'red'
        if self.is_online():
            text = 'ONLINE'
            color = 'green'

        return format_html("<span style='color: " + color + ";'>" + text + "</span>")
    online_status.short_description = _('Online Status')

    def get_routes(self):
        routes = []
        net_routes = NetworkRoutes.objects.filter(network=self.network, gateway=self.ipaddress)
        text = format_html('<small>' + '<br />'.join([str(p) for p in net_routes]) + '</small>')
        return text
    get_routes.short_description = _('Routes')

    def get_routes_plain(self):
        routes = []
        net_routes = NetworkRoutes.objects.filter(network=self.network, gateway=self.ipaddress)
        text = ', '.join([str(p) for p in net_routes])
        return text
    get_routes_plain.short_description = _('Local Routes')

    def is_mqtt_online(self):
        online_status = False
        if self.mqtt:
            online_status = self.mqtt.is_online()
        return online_status
    is_mqtt_online.short_description = _('Internet Online')

    def get_alarms(self):
        result = []
        if self.organization:
            if self.organization.features.is_nms:
                #rules = check_members_vs_rules(self, self.is_online())
                rules = check_members_vs_rules(self, True)
                for rule in rules:
                    result.append(rule.item.item_id)

        return result

    def memory_usage(self):
        result = 0.0
        if self.mqtt:
            result = round(self.mqtt.memory_usage, 1)

        return result

    def cpu_usage(self):
        result = 0.0
        if self.mqtt:
            load_1, load_5, load_15 = self.mqtt.get_cpu_usage()
            result = round(load_5, 1)

        return result

    def packet_loss(self):
        result = -1.0
        if self.mqtt:
            result = round(self.mqtt.get_packet_loss(), 1)

        return result

    def round_trip(self):
        result = -1.0
        if self.mqtt:
            result = round(self.mqtt.get_round_trip(), 1)

        return result

    def ipaddress_ts(self):
        result = None
        if self.mqtt:
            result = self.mqtt.ipaddress_ts

        return result

    def serialnumber(self):
        result = None
        if self.mqtt:
            result = self.mqtt.serialnumber

        return result

    def model_release(self):
        text = None
        if self.mqtt:
            mqtt = self.mqtt
            alarms = self.get_alarms()
            updated_at = timezone.localtime(mqtt.updated_at).strftime("%d-%m-%Y, %H:%M:%S")
            is_rcall = "icon-yes.svg" if mqtt.is_rcall else "icon-no.svg"

            ''' First Line: Model and CPU Core'''
            first_line = "<small>{} ({})</small>".format(mqtt.model, mqtt.num_core)

            ''' Second Line: SerialNumber and Release Version'''
            second_line_var = mqtt.serialnumber + ' - ' + mqtt.release_version if mqtt.serialnumber else mqtt.release_version

            second_line = ""
            if second_line_var:
                second_line = "<br /><small>"
                second_line += "{} <img src='/static/admin/img/{}'>".format(
                        second_line_var, is_rcall) if mqtt.is_rcall else second_line_var
                second_line += "</small>"

            ''' Third Line: SwitchPortUp and PortStatus'''
            third_line = ""
            if self.mqtt.switchport_up:
                third_line += "<br /><small>"
                third_line += "<span>SwPortUP: {}</span>".format(self.mqtt.switchport_up)
                third_line += "</small>"

            if self.mqtt.port_status:
                third_line += "<br /><small>"
                third_line += "<span>PortStat: {}</span>".format(self.mqtt.port_status)
                third_line += "</small>"

            ''' Fourth Line: Uptime, CPU and Memory '''
            fourth_line = "<br /><small>"

            ''' UPTIME '''
            uptime_string = self.mqtt.get_uptime_string()
            fourth_line += "<span>UP: {}</span>".format(uptime_string)

            ''' CPU '''
            item_id = 'cpu_usage'
            value = self.cpu_usage()
            color = 'red' if item_id in alarms else ''
            fourth_line += " - <span style='color: {};'>CPU: {}%</span>".format(color, value)

            ''' MEMORY '''
            item_id = 'memory_usage'
            value = self.memory_usage()
            color = 'red' if item_id in alarms else ''
            fourth_line += " - <span style='color: {};'>MEM: {}%</span>".format(color, value)

            ''' PACKET LOSS '''
            item_id = 'packet_loss'
            value_pl = self.packet_loss()
            #value_rt = self.round_trip()
            color = 'red' if item_id in alarms else ''
            #if value_rt:
            if value_pl >= 0:
                fourth_line += "<br /><span style='color: {};'>PL: {}% - </span>".format(color, value_pl)

            ''' ROUND_TRIP '''
            item_id = 'round_trip'
            #value = self.round_trip()
            value_rt = self.round_trip()
            color = 'red' if item_id in alarms else ''
            if value_rt > 0:
                fourth_line += "<span style='color: {};'>RT: {}ms<span>".format(color, value_rt)

            fourth_line += "</small>"

            ''' Fifth line QUOTA FIRST '''
            fifth_line = ""

            quota_current, quota_total, quota_day = self.mqtt.get_quota_first()

            #if not quota_current==0 and not quota_total==0 and not quota_day==0:
            quota_current = quota_current / 1024
            if not quota_total==0:
                item_id = 'quota_first_gb'
                color = 'red' if item_id in alarms else ''
                quota_text = ""
                #color = '' if quota_current > settings.QUOTA_GB_WARNING else 'red'
                quota_text += "<span style='color: {};'>{}GB</span>".format(color, quota_current)

                quota_text += "<span>/{}GB/</span>".format(quota_total)

                item_id = 'quota_first_day'
                color = 'red' if item_id in alarms else ''
                #color = '' if quota_day > settings.QUOTA_DAY_WARNING else 'red'
                quota_text += "<span style='color: {};'>{}Hari</span>".format(color, quota_day)

                fifth_line = "<br /><small>QUO: {}</small>".format(quota_text)

            quota_current_prev, quota_total_prev, quota_day_prev = self.mqtt.get_quota_first_prev()
            quota_current_prev = quota_current_prev / 1024

            if not quota_total_prev==0:
                item_id = 'quota_first_high_gb'
                color = 'red' if item_id in alarms else ''
                quota_text_prev = ""
                #color = '' if quota_current > settings.QUOTA_GB_WARNING else 'red'
                quota_text_prev += "<span style='color: {};'>{}GB</span>".format(color, quota_current_prev)

                quota_text_prev += "<span>/{}GB/</span>".format(quota_total_prev)

                quota_text_prev += "<span>{}Hari</span>".format(quota_day_prev)

                fifth_line += "<br /><small>QUO_PREV: {}</small>".format(quota_text_prev)

            sixth_line = ''
            vnstat_text = self.quota_vnstat()
            if vnstat_text != "":
                sixth_line = "<br /><small>QUSE: {}</small>".format(vnstat_text)

            ''' Combine All Lines '''
            if self.is_mqtt_online():
                text = format_html(
                        first_line + 
                        second_line + 
                        third_line + 
                        fourth_line +
                        fifth_line +
                        sixth_line)

            else:
                text = format_html(
                        first_line + 
                        second_line + 
                        third_line + 
                        fourth_line +
                        fifth_line +
                        sixth_line +
                        "<br /><small style='color: red;'>LU: {} ago</span></small>", readable_timedelta(mqtt.updated_at))

        return text
    model_release.short_description = _('Parameters')

    def member_name_with_address(self):
        text = self.name
        if self.address:
            address_html = format_html(self.address.replace(',', '<br />'))
            text = format_html('{}<br /><small>{}</small>', self.name, address_html)
        return text
    member_name_with_address.short_description = _('Member Name')
    member_name_with_address.admin_order_field = 'name'

    def switchport_up(self):
        text = ''
        if self.mqtt:
            if self.mqtt.switchport_up:
                text = self.mqtt.switchport_up

        return text
    switchport_up.short_description = _('Switch Port UP')

    def quota_vnstat(self):
        text = ''
        if self.mqtt:
            rx_usage_value, tx_usage_value, total_usage_value = self.mqtt.get_quota_vnstat()
            total_unit, total_value = calculate_bandwidth_unit(total_usage_value)
            if total_value:  # Only show if not 0
                text = str(round(total_value, 2)) + total_unit

        return text
    quota_vnstat.short_description = _('Quota Usage')


    def rssi(self):
        text = 'N/A'
        color = 'black'
        if self.mqtt:
            rssi_signal = self.mqtt.rssi()
            if rssi_signal <= 65:
                text = 'EXCELLENT'
                color = 'blue'
            elif rssi_signal > 65 and rssi_signal <= 80:
                text = 'GOOD'
                color = 'green'
            elif rssi_signal != 99999:
                text = 'NOT GOOD'
                color = 'red'

        #return text
        return format_html("<span style='color: {};'>{}</span>", color, text)

    rssi.short_description = _('RSSI Signal')

