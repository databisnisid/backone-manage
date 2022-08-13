from django.db import models
from django.contrib.auth.models import User
from networks.models import Networks
from crum import get_current_user
from django.utils.translation import gettext as _
from django.utils.html import format_html
from controllers.backend import Zerotier
from django.core.exceptions import ObjectDoesNotExist
from config.utils import to_dictionary, get_user
from ipaddress import ip_address, ip_network
from django.core.exceptions import ValidationError


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
            return {'user': user}
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
        on_delete=models.CASCADE,
        verbose_name=_('Owner')
    )

    is_bridge = models.BooleanField(_('Bridge'), default=False)
    is_authorized = models.BooleanField(_('Authorized'), default=True)
    #ipaddress = models.GenericIPAddressField(_('IP Address'), blank=True, null=True)
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
        try:
            self.user
        except ObjectDoesNotExist:
            self.user = get_user()

        self.user = self.network.user

        # Zerotier
        zt = Zerotier(self.network.controller.uri, self.network.controller.token)

        # Authorized member
        if self.is_authorized:
            member_info = zt.authorize_member(self.network.network_id, self.member_id)
        else:
            member_info = zt.authorize_member(self.network.network_id, self.member_id, authorized=False)

        # Set Bridge
        if self.is_bridge:
            data = {'activeBridge': True}
        else:
            data = {'activeBridge': False}
        member_info = zt.set_member(self.network.network_id, self.member_id, data)

        # Assign IP Address
        if self.ipaddress is not None:
            self.ipaddress = self.ipaddress.replace(' ', '')
            ip_address_list = []
            for ipaddress in self.ipaddress:
                ip_address_list.append(ipaddress)
            data = {'ipAssignments': ip_address_list}
            member_info = zt.set_member(self.network.network_id, self.member_id, data)

        if 'address' in member_info:
            if not self.name:
                self.name = 'NET: ' + self.network.name + ' MEMBER: ' + member_info['id']

            # self.is_authorized = True
            self.configuration = member_info
            self.member_id = member_info['id']

            if len(member_info['ipAssignments']) != 0:
                self.ipaddress = member_info['ipAssignments'][0]

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
        # TODO
        # CHECK: For multiple IP in self.ipaddress
        '''
        try:
            ip_address(self.ipaddress)
            ipaddress_network = '{}/{}'.format(self.network.ip_assignment, self.network.ip_assignment_netmask)
            if ip_address(self.ipaddress) not in ip_network(ipaddress_network):
                raise ValidationError({'ipaddress': _('IP address should be in segment ' + ipaddress_network)})


            # Second Raise
            members = Members.objects.filter(ipaddress=self.ipaddress).exclude(member_id=self.member_id)
            if members:
                raise ValidationError({'ipaddress': _('IP address ' + self.ipaddress + ' is already used!')})

        except ValueError:
            pass
        '''
        # TODO
        # Check for list IP_address
        if self.ipaddress is not None:
            self.ipaddress = self.ipaddress.replace(' ', '')

            #print(self.network.ip_address_networks)
            ip_address_lists = self.ipaddress.split(',')

            for ip_address_list in ip_address_lists:
                print(ip_address_list)
                try:
                    ip_address(ip_address_list)
                except ValueError:
                    raise ValidationError({'ipaddress': _('Wrong Format')})

        # New Block Validation compare to ip_network
            if self.network.ip_address_networks is not None:
                #print(self.network.ip_address_networks)
                ip_network_lists = self.network.ip_address_networks.split(',')

                is_ipaddress_in_network = False
                for ip_network_list in ip_network_lists:
                    print(ip_network_list)
                    for ip_address_list in ip_address_lists:
                        if ip_address(ip_address_list) in ip_network(ip_network_list):
                            is_ipaddress_in_network = True

                if not is_ipaddress_in_network:
                    raise ValidationError({'ipaddress': _('IP address should be in segment ' +
                                                          self.network.ip_address_networks)})

                # Second Raise
                for ip_address_list in ip_address_lists:
                    members = Members.objects.filter(
                        ipaddress__contains=ip_address_list
                    ).exclude(member_id=self.member_id)

                    if members:
                        raise ValidationError({'ipaddress': _('IP address ' + self.ipaddress + ' is already used!')})
                        break
            else:
                raise ValidationError(_('First, please setup IP Network in ' + self.network.name))

    def list_peers(self):
        peers = to_dictionary(self.peers.peers)
        if 'paths' in peers and len(peers['paths']) != 0:
            paths = peers['paths']
            ip_peers = []
            for path in paths:
                ip_path = path['address'].split('/')
                if ip_path[0] not in ip_peers:
                    ip_peers.append(ip_path[0])
                #[ip_peers.append(peer['address']) for peer in paths]

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
            #latency = str(int(peers['latency']) * -1) if int(peers['latency']) < 0 else peers['latency']
            if latency < 0:
                direct_or_relay = 'RELAY'
            else:
                direct_or_relay = 'DIRECT'
            #latency = str(peers['latency'])
            text = format_html("<small style='color: green;'>ONLINE ({})<br />{}({}ms)<br />{}</small>",
                               version, peers['role'], str(latency), direct_or_relay)
        else:
            controller_configuration = to_dictionary(self.network.controller.configuration)
            version = controller_configuration['version']
            if self.member_id == controller_configuration['address']:
                text = format_html("<small style='color: blue;'>CONTROLLER ({})</small>", version)
            else:
                text = format_html("<small style='color: red;'>OFFLINE</small>")

        return text

    member_status.short_description = _('Status')

        #return ",".join([str(p) for p in self.networks.all()])
