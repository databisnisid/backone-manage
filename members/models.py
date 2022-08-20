from django.db import models
from accounts.models import User, Organizations
from networks.models import Networks
from django.utils.translation import gettext as _
from django.utils.html import format_html
from controllers.backend import Zerotier
from django.core.exceptions import ObjectDoesNotExist
from config.utils import to_dictionary
from ipaddress import ip_address, ip_network
from django.core.exceptions import ValidationError
from crum import get_current_user


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

    configuration = models.TextField(_('Configuration'), blank=True)
    peers = models.ForeignKey(
        MemberPeers,
        on_delete=models.CASCADE,
        verbose_name=_('Peers')
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

        return super(Members, self).save()

    def clean(self):
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

                is_ipaddress_in_network = False
                for ip_address_list in ip_address_lists:
                    for ip_network_list in ip_network_lists:
                        if ip_address(ip_address_list) in ip_network(ip_network_list):
                            is_ipaddress_in_network = True
                            break
                        else:
                            is_ipaddress_in_network = False

                if not is_ipaddress_in_network:
                    raise ValidationError({'ipaddress': _('IP address should be in segment ' +
                                                          self.network.ip_address_networks)})

                # Second Raise
                for ip_address_list in ip_address_lists:

                    members = Members.objects.filter(
                        ipaddress__contains=ip_address_list).exclude(member_id=self.member_id)

                    if members:
                        raise ValidationError(
                            {'ipaddress': _('IP address ' + ip_address_list + ' is already used!')})
            else:
                raise ValidationError(_('First, please setup IP Network in ' + self.network.name))

    def list_ipaddress(self):
        text = ''
        if self.ipaddress is not None:
            ipaddress_list = self.ipaddress.split(',')
            text = format_html('<br />'.join([str(p) for p in ipaddress_list]))

        return text
    list_ipaddress.short_description = _('IP Address')

    def list_peers(self):
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
            peers = to_dictionary(self.peers.peers)

            if self.member_id == controller_configuration['address']:
                version = controller_configuration['version']
                text = format_html("<small style='color: blue;'>CONTROLLER ({})</small>", version)
            elif 'role' in self.peers.peers and 'latency' in self.peers.peers \
                    and 'version' in self.peers.peers: # and int(self.peers.peers['latency']) == -1:
                text = format_html("<small style='color: green;'>RELAY ({})</small>", peers['version'])
            else:
                text = format_html("<small style='color: red;'>OFFLINE</small>")

        return text

    member_status.short_description = _('Status')