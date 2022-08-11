from django.db import models
from django.contrib.auth.models import User
from controllers.models import Controllers, UserControllers
from crum import get_current_user
from django.utils.translation import gettext as _
from django.utils.html import format_html
from controllers.backend import Zerotier
from django.core.exceptions import ObjectDoesNotExist
from config.utils import to_dictionary, get_user
from ipaddress import ip_address, ip_network
from django.core.exceptions import ValidationError


NETMASK = [
    (24, '24'),
    (23, '23'),
    (22, '22'),
    (21, '21'),
    (20, '20'),
    (19, '19'),
    (18, '18'),
    (17, '17'),
    (16, '16'),
    (15, '15'),
    (14, '14'),
    (13, '13'),
    (12, '12'),
    (11, '11'),
    (10, '10'),
    (9, '9'),
    (8, '8'),
]


class Networks(models.Model):
    name = models.CharField(_('Name'), max_length=50)
    description = models.TextField(_('Description'), blank=True)
    network_id = models.CharField(_('Network ID'), max_length=50, unique=True)

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name=_('Owner'),
    )

    controller = models.ForeignKey(
        Controllers,
        on_delete=models.CASCADE,
    )
    ip_assignment = models.GenericIPAddressField(_('IP Assignment'), blank=True, null=True)
    ip_assignment_netmask = models.IntegerField(_('IP Netmask'), choices=NETMASK, default=24)

    # NOTE: This will be improvement in the future, to support many ip assigment in Network
    #ip_address_netmask = models.CharField(_('IP Network'), max_length=100, blank=True)

    configuration = models.TextField(_('Configuration'), blank=True)
    route = models.TextField(_('Route'), blank=True)

    created_at = models.DateTimeField(auto_now=False, auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True, auto_now_add=False)

    class Meta:
        db_table = 'networks'
        verbose_name = 'network'
        verbose_name_plural = 'networks'

    def __str__(self):
        return '%s' % self.name

    def delete(self, using=None, keep_parents=False):
        zt = Zerotier(self.controller.uri, self.controller.token)
        zt.delete_network(self.network_id)
        return super(Networks, self).delete()

    def save(self):
        try:
            self.user
        except ObjectDoesNotExist:
            self.user = get_user()
            '''
            user = get_current_user()
            if user:
                self.user = user
            else:
                user = User.objects.get(id=1)
                self.user = user
            '''

        # Assign controller
        user_controller = UserControllers.objects.get(user=self.user)
        self.controller = user_controller.controller

        zt = Zerotier(self.controller.uri, self.controller.token)
        result = zt.list_networks()

        if self.network_id is not None and self.network_id not in result:
            result = zt.add_network()
        else:
            result = zt.get_network_info(self.network_id)

        #print(result)

        if 'nwid' in result:
            self.network_id = result['nwid']
            if not self.name:
                if not result['name']:
                    self.name = self.network_id + ' Network'
                else:
                    self.name = result['name']

            #print(self.name, result)

            result['name'] = self.name
            result = zt.set_network_name(self.network_id, self.name)

            #print(result)

            try:
                """
                Check if ip_assignment is entered and valid
                """
                ip_address(self.ip_assignment)
                ip_assignment = '{0}/{1}'.format(str(self.ip_assignment), str(self.ip_assignment_netmask))

                #route_index = 0
                if 'routes' in result:
                    routes = result['routes']
                    route_index = -1
                    for i in range(len(routes)):
                        if routes[i]['via'] is None:
                            route_index = i
                            break

                    """ If route is found """
                    if route_index >= 0:
                        routes[route_index]['target'] = ip_assignment
                    else:
                        route = {'target': ip_assignment, 'via': ''}
                        routes.insert(0, route)

                else:
                    routes = []
                    route = {'target': ip_assignment, 'via': ''}
                    routes.insert(0, route)

                routes_json = {'routes': routes}
                result = zt.set_network(self.network_id, routes_json)

            except ValueError:
                #route_index = 0
                #print('ValueError', result)
                if 'routes' in result:
                    routes = result['routes']
                    #print(routes)
                    route_index = -1
                    for i in range(len(routes)):
                        if routes[i]['via'] is None:
                            route_index = i
                            break

                    if route_index >= 0:
                        if self.created_at is None:
                            """
                            if new record and have route in configuration
                            then add the route into ip_assigment
                            """
                            ip_route = routes[route_index]['target']
                            ip_target = ip_route.split('/')
                            self.ip_assignment = ip_target[0]
                            self.ip_assignment_netmask = ip_target[1]
                        else:
                            routes.pop(route_index)
                            routes_json = {'routes': routes}
                            result = zt.set_network(self.network_id, routes_json)

            #print(result)

            #self.network_id = result['nwid']
            self.configuration = result
            self.route = result['routes']

        return super(Networks, self).save()

    def ip_allocation(self):
        if self.ip_assignment is not None:
            return '%s/%s' % (self.ip_assignment, self.ip_assignment_netmask)
        else:
            return ''
    ip_allocation.short_description = 'IP Allocation'


class NetworkRoutes(models.Model):
    def limit_choices_to_current_user():
        """
        limit the choice of foreignkey to current user
        :return:
        """
        user = get_current_user()
        if not user.is_superuser:
            return {'user': user}
        else:
            return {}

    ip_network = models.GenericIPAddressField(_('IP Network'))
    ip_netmask = models.IntegerField(_('Netmask'), choices=NETMASK, default=24)
    gateway = models.GenericIPAddressField(_('Gateway'), null=True)
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

    created_at = models.DateTimeField(auto_now=False, auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True, auto_now_add=False)

    class Meta:
        db_table = 'network_routes'
        verbose_name = 'network route'
        verbose_name_plural = 'network routes'

    def __str__(self):
        return '%s/%s' % (self.ip_network, self.ip_netmask)

    def save(self):
        try:
            self.user
        except ObjectDoesNotExist:
            self.user = get_user()

        self.user = self.network.user

        ip_target = '{}/{}'.format(str(self.ip_network), str(self.ip_netmask))
        zt = Zerotier(self.network.controller.uri, self.network.controller.token)
        result = zt.get_network_info(self.network.network_id)
        routes = result['routes']
        #print(routes)

        is_already_there = False
        for i in range(len(routes)):
            if routes[i]['target'] == ip_target:
                is_already_there = True

        if not is_already_there:
            route_add = {'target': ip_target, 'via': self.gateway}
            routes.append(route_add)
            routes_new = {'routes': routes}
            print(routes_new)
            zt.set_network(self.network.network_id, routes_new)

            network = Networks.objects.get(id=self.network.id)
            network.save()

        #print(routes)

        return super(NetworkRoutes, self).save()

    def delete(self, using=None, keep_parents=False):
        ip_target = '{}/{}'.format(str(self.ip_network), str(self.ip_netmask))
        zt = Zerotier(self.network.controller.uri, self.network.controller.token)
        result = zt.get_network_info(self.network.network_id)
        routes = result['routes']

        index = -1
        for i in range(len(routes)):
            if routes[i]['target'] == ip_target:
                index = i
                break

        # If found the ip_target, remove it
        if index >= 0:
            routes.pop(index)
            routes_new = {'routes': routes}
            print(routes_new)
            zt.set_network(self.network.network_id, routes_new)

            network = Networks.objects.get(id=self.network.id)
            network.save()
            
        return super(NetworkRoutes, self).delete()

    def clean(self):
        try:
            NetworkRoutes.objects.get(ip_network=self.ip_network,
                                      ip_netmask=self.ip_netmask,
                                      network=self.network)
            ip_target = '{}/{} is already used!'.format(str(self.ip_network), str(self.ip_netmask))
            raise ValidationError({'ip_network': _(ip_target)})
        except ObjectDoesNotExist:
            pass

        num_routes = NetworkRoutes.objects.filter(network=self.network).count()
        if num_routes == 32:
            raise ValidationError(_("Maximum routes is reached!"))


class NetworkRules(models.Model):
    def limit_choices_to_current_user():
        user = get_current_user()
        if not user.is_superuser:
            return {'user': user}
        else:
            return {}

    network = models.OneToOneField(
        Networks,
        on_delete=models.CASCADE,
        limit_choices_to=limit_choices_to_current_user,
        verbose_name=_('Network')
    )
    rules = models.TextField(_('Network Rules'), blank=True)

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name=_('Owner')
    )

    created_at = models.DateTimeField(auto_now=False, auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True, auto_now_add=False)

    class Meta:
        db_table = 'network_rules'
        verbose_name = 'network rule'
        verbose_name_plural = 'network rules'

    def __str__(self):
        return '%s' % self.network

    def save(self):
        try:
            self.user
        except ObjectDoesNotExist:
            self.user = get_user()

        self.user = self.network.user

        return super(NetworkRules, self).save()


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
    ipaddress = models.GenericIPAddressField(_('IP Address'), blank=True, null=True)
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
            data = {'ipAssignments': [self.ipaddress]}
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
        try:
            ip_address(self.ipaddress)
            ipaddress_network = '{}/{}'.format(self.network.ip_assignment, self.network.ip_assignment_netmask)
            if ip_address(self.ipaddress) not in ip_network(ipaddress_network):
                raise ValidationError({'ipaddress': _('IP address should be in segment ' + ipaddress_network)})

            members = Members.objects.filter(ipaddress=self.ipaddress).exclude(member_id=self.member_id)
            if members:
                raise ValidationError({'ipaddress': _('IP address ' + self.ipaddress + ' is already used!')})

        except ValueError:
            pass

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
