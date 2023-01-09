from datetime import datetime
from crum import get_current_user
from django.db import models
from django.utils import timezone
from accounts.models import User, Organizations
from networks.models import Networks
from django.utils.translation import gettext as _
from django.utils.html import format_html
from controllers.backend import Zerotier
from django.core.exceptions import ObjectDoesNotExist
from config.utils import to_dictionary, get_cpu_usage, get_uptime_string, get_string_between, readable_timedelta
from ipaddress import ip_address, ip_network
from django.core.exceptions import ValidationError
from mqtt.models import Mqtt


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
    serialnumber = models.CharField(_('SN'), max_length=100, blank=True, null=True)


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
        # Check if member_id is already in this network

        if self.member_id:
            if self.id is None:
                try:
                    Members.objects.get(member_id=self.member_id, network=self.network)
                    raise ValidationError({'member_id': _('Member ID already exist in this network!')})
                except ObjectDoesNotExist:
                    pass

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
            for path in paths:
                ip_path = path['address'].split('/')
                if ip_path[0] not in ip_peers:
                    ip_peers.append(ip_path[0])

            result = '<br />'.join([str(p) for p in ip_peers])
            return format_html('<small>' + result + '</small>')
        else:
            return ''

    list_peers.short_description = _('Peers')

    def member_status(self):
        peers = to_dictionary('{}')
        if self.peers:
            peers = to_dictionary(self.peers.peers)

        if 'paths' in peers and len(peers['paths']) != 0:
            version = peers['version']
            latency = peers['latency']

            if latency < 0:
                direct_or_relay = 'RELAY'
            else:
                direct_or_relay = 'DIRECT'

            text = format_html("<small style='color: green;'>ONLINE ({})<br />{}({}ms)<br />{}</small>",
                               version, peers['role'], str(latency), direct_or_relay)
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
                    text = format_html("<small style='color: green;'>RELAY ({})</small>", peers['version'])
                else:
                    text = format_html("<small style='color: red;'>OFFLINE</small>")
            else:
                text = format_html("<small style='color: red;'>OFFLINE</small>")

        return text

    member_status.short_description = _('Status')

    def is_online(self):
        online_status = False
        peers = to_dictionary('{}')
        if self.peers:
            peers = to_dictionary(self.peers.peers)
        if 'paths' in peers and len(peers['paths']) != 0 and self.ipaddress:
            online_status = True
        return online_status
    is_online.short_description = _('BackOne Online')

    def is_mqtt_online(self):
        online_status = False
        try:
            mqtt = Mqtt.objects.get(member_id=self.member_id)
            now = timezone.now()
            delta = now - timezone.localtime(mqtt.updated_at)
            if delta.seconds < 660:
               online_status = True
        except ObjectDoesNotExist:
            pass

        return online_status
    is_mqtt_online.short_description = _('Internet Online')

    def memory_usage(self):
        result = 0.0
        try:
            mqtt = Mqtt.objects.get(member_id=self.member_id)
            result = mqtt.memory_usage
        except ObjectDoesNotExist:
            pass

        return result

    def cpu_usage(self):
        result = 0.0
        try:
            mqtt = Mqtt.objects.get(member_id=self.member_id)
            if mqtt.uptime:
                load_1, load_5, load_15 = get_cpu_usage(mqtt.uptime, mqtt.num_core)
            else:
                load_1 = load_5 = load_15 = 0.0
            result = round(load_5, 1)
        except ObjectDoesNotExist:
            pass

        return result

    def model_release(self):
        text = None
        try:
            mqtt = Mqtt.objects.get(member_id=self.member_id)
            if self.mqtt is None:
                self.mqtt = mqtt
                self.save()
            model = mqtt.model
            release_version = mqtt.release_version
            updated_at = timezone.localtime(mqtt.updated_at).strftime("%d-%m-%Y, %H:%M:%S")
            #is_rcall = 'R' if mqtt.is_rcall else 'S'
            is_rcall = "icon-yes.svg" if mqtt.is_rcall else "icon-no.svg"
            uptime = mqtt.uptime
            serialnumber = mqtt.serialnumber
            num_core = mqtt.num_core
            memory_usage = mqtt.memory_usage

            first_line = '{} ({})'.format(model, num_core)
            second_line = serialnumber + ' - ' + release_version if serialnumber else release_version
            if uptime:
                load_1, load_5, load_15 = get_cpu_usage(uptime, num_core)
            else:
                load_1 = load_5 = load_15 = 0.0

            if self.is_mqtt_online():
                text = format_html("<small style='color: green;'>{}<br />{} <img src='/static/admin/img/{}'><br />UP: {} - CPU: {}% - MEM: {}%</small>", first_line, second_line, is_rcall, get_uptime_string(uptime), round(load_5, 1), round(memory_usage, 1))
                if load_5 > 50 or memory_usage > 50:
                    text = format_html("<small style='color: green;'>{}<br />{} <img src='/static/admin/img/{}'><br />UP: {} - <span style='color: red; font-weight: bold;'>CPU: {}% - MEM: {}%</span></small>", first_line, second_line, is_rcall, get_uptime_string(uptime), round(load_5, 1), round(memory_usage, 1))

            else:
                text = format_html("<small style='color: red;'>{}<br />{} <br />LO: {} ago</small>", first_line, second_line, readable_timedelta(mqtt.updated_at))
        except ObjectDoesNotExist:
            pass
            #model = release_version = None

        return text
    model_release.short_description = _('Model, SN, Release')

