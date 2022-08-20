from django.db import models
from accounts.models import User, Organizations
from controllers.models import Controllers
from crum import get_current_user
from django.utils.translation import gettext as _
from django.utils.html import format_html
from controllers.backend import Zerotier
from django.core.exceptions import ObjectDoesNotExist
from ipaddress import ip_network
from django.core.exceptions import ValidationError
import os
import subprocess
from config import settings

''' Sample of Validator'''
'''
def validate_even(value):
    if value % 2 != 0:
        raise ValidationError(
            _('%(value)s is not an even number'),
            params={'value': value},
        )
even_field = models.IntegerField(validators=[validate_even])
'''


class Networks(models.Model):
    """
    "ipAssignmentPools": [
    {
        "ipRangeEnd": "192.168.64.200",
        "ipRangeStart": "192.168.64.10"
    }
    ],
    "v4AssignMode": {
        "zt": true
    },
    """
    name = models.CharField(_('Name'), max_length=50)
    description = models.TextField(_('Description'), blank=True)
    network_id = models.CharField(_('Network ID'), max_length=50, unique=True)

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

    controller = models.ForeignKey(
        Controllers,
        on_delete=models.CASCADE,
    )

    # NOTE: This will be improvement in the future, to support many ip assigment in Network
    ip_address_networks = models.CharField(_('IP Networks'), max_length=100,
                                           blank=True, null=True,
                                           help_text='Example: 192.168.0.0/24, 10.0.0.0/24')
    '''
    This auto assign is can be done later.
    '''
    '''
    is_auto_assign = models.BooleanField(_('Auto Assign IP'), default=False)
    ip_pools = models.CharField(_('IP Pools'), blank=True, null=True,
                                help_text=_('Example: 192.168.0.10-192.168.0.200'))
    '''
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
        '''
        try:
            self.user
            if self.user is None:
                #self.user = get_user()
                self.user = get_current_user()
        except ObjectDoesNotExist:
            self.user = get_user()
        '''

        if self.user is None:
            self.user = get_current_user()

        print('Network Model', self.user)

        #if self.organization is None:
        self.organization = self.user.organization

        try:
            self.controller
            if self.controller is None:
                self.controller = self.user.organization.controller
        except ObjectDoesNotExist:
            self.controller = self.user.organization.controller

        zt = Zerotier(self.controller.uri, self.controller.token)
        result = zt.list_networks()

        if self.network_id is not None and self.network_id not in result:
            result = zt.add_network()
        else:
            result = zt.get_network_info(self.network_id)

        if 'nwid' in result:
            self.network_id = result['nwid']
            if not self.name:
                if not result['name']:
                    self.name = self.network_id + ' Network'
                else:
                    self.name = result['name']

            result['name'] = self.name
            data = {'name': self.name}

            # Working on IP Network array
            if self.ip_address_networks is not None:
                self.ip_address_networks = self.ip_address_networks.replace(' ', '')
                ip_network_lists = self.ip_address_networks.split(',')
                # if len(ip_network_lists) >= 0:
                try:
                    for ip_network_list in ip_network_lists:
                        ip_network(ip_network_list)
                    is_ip_networks = True
                except ValueError:
                    is_ip_networks = False

                if is_ip_networks:
                    if 'routes' in result:
                        routes = result['routes']

                        ''' Delete all default route'''
                        j = 0
                        for i in range(len(routes)):
                            if routes[i-j]['via'] is None:
                                routes.pop(i - j)
                                j += 1

                        for i in range(len(ip_network_lists)):
                            route = {'target': ip_network_lists[i], 'via': ''}
                            routes.insert(i, route)

                        data['routes'] = routes
            else:
                # If no route
                routes = result['routes']
                j = 0
                for i in range(len(routes)):
                    if routes[i-j]['via'] is None:
                        routes.pop(i-j)
                        j += 1
                data['routes'] = routes

            print('Network', self.network_id, data)
            result = zt.set_network(self.network_id, data)
            self.configuration = result
            self.route = result['routes']

        return super(Networks, self).save()

    def clean(self):
        if self.ip_address_networks is not None:
            self.ip_address_networks = self.ip_address_networks.replace(' ', '')

            ip_network_lists = self.ip_address_networks.split(',')

            try:
                for ip_network_list in ip_network_lists:
                    ip_network(ip_network_list)
            except ValueError:
                raise ValidationError({'ip_address_networks': _('IP Format is not correct!')})

    def ip_allocation(self):
        text = ''
        if self.ip_address_networks is not None:
            ip_network_lists = self.ip_address_networks.split(',')
            text = format_html('<br />'.join([str(p) for p in ip_network_lists]))
        return text
    ip_allocation.short_description = 'IP Allocations'


class NetworkRoutes(models.Model):
    def limit_choices_to_current_user():
        """
        limit the choice of foreignkey to current user
        :return:
        """
        user = get_current_user()
        print('Network User', user)
        if not user.is_superuser:
            if user.organization.is_no_org:
                return {'user': user}
            else:
                return {'organization': user.organization}
        else:
            return {}

    ip_network = models.CharField(_('IP Network'), max_length=50,
                                  help_text=_('Example: 192.168.0.0/24'))
    gateway = models.GenericIPAddressField(_('Gateway'), null=True)
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

    created_at = models.DateTimeField(auto_now=False, auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True, auto_now_add=False)

    class Meta:
        db_table = 'network_routes'
        verbose_name = 'network route'
        verbose_name_plural = 'network routes'

    def __str__(self):
        return '%s' % self.ip_network

    def save(self):
        self.user = self.network.user
        self.organization = self.network.organization

        if self.ip_network:
            self.ip_network = self.ip_network.replace(' ', '')

        zt = Zerotier(self.network.controller.uri, self.network.controller.token)
        result = zt.get_network_info(self.network.network_id)
        routes = result['routes']

        is_already_there = False
        for i in range(len(routes)):
            if routes[i]['target'] == self.ip_network:
                is_already_there = True
                break

        if not is_already_there:
            route_add = {'target': self.ip_network, 'via': self.gateway}
            routes.append(route_add)
            routes_new = {'routes': routes}
            print(routes_new)
            zt.set_network(self.network.network_id, routes_new)

            if self.gateway is not None:
                network = Networks.objects.get(id=self.network.id)
                network.save()

        return super(NetworkRoutes, self).save()

    def delete(self, using=None, keep_parents=False):
        ip_target = self.ip_network
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
        if self.ip_network is not None:
            try:
                ip_network(self.ip_network)
                try:
                    NetworkRoutes.objects.get(ip_network=self.ip_network,
                                              network=self.network)
                    raise ValidationError({'ip_network': _('IP Network is already used!')})
                except ObjectDoesNotExist:
                    pass

                num_routes = NetworkRoutes.objects.filter(network=self.network).count()
                if num_routes == 32:
                    raise ValidationError(_("Maximum routes is reached!"))

            except ValueError:
                raise ValidationError(_("Wrong IP Format!"))


DEFAULT_RULE_DEFINITION = """
# This is a default rule set that allows IPv4 and IPv6 traffic.
# You can edit as needed. If your rule set gets large we recommend
# cutting and pasting it somewhere to keep a backup.

# Drop all Ethernet frame types that are not IPv4 or IPv6
drop
	not ethertype 0x0800 # IPv4
	not ethertype 0x0806 # IPv4 ARP
	#not ethertype 0x86dd # IPv6
;

# Capability: outgoing SSH
#cap ssh
#	id 1000
#	accept
#		ipprotocol tcp
#		dport 22
#	;
#;

# A tag indicating which department people belong to
#tag department
#	id 1000
#	enum 100 sales
#	enum 200 marketing
#	enum 300 accounting
#	enum 400 engineering
#;

# Accept all traffic between members of the same department
#accept
#	tdiff department 0
#;

# You can insert other drop, tee, etc. rules here. This rule
# set ends with a blanket accept, making it permissive by
# default.

accept;
"""

DEFAULT_RULE = """
[
   {
    "type": "MATCH_ETHERTYPE",
    "not": true,
    "or": false,
    "etherType": 2048
   },
   {
    "type": "MATCH_ETHERTYPE",
    "not": true,
    "or": false,
    "etherType": 2054
   },
   {
    "type": "MATCH_ETHERTYPE",
    "not": true,
    "or": false,
    "etherType": 34525
   },
   {
    "type": "ACTION_DROP"
   },
   {
    "type": "ACTION_ACCEPT"
   }
]
"""


class NetworkRules(models.Model):
    def limit_choices_to_current_user():
        """
        limit the choice of foreignkey to current user
        :return:
        """
        user = get_current_user()
        print('Network User', user)
        if not user.is_superuser:
            if user.organization.is_no_org:
                return {'user': user}
            else:
                return {'organization': user.organization}
        else:
            return {}

    name = models.CharField(_('Name'), max_length=50)
    network = models.OneToOneField(
        Networks,
        on_delete=models.CASCADE,
        limit_choices_to=limit_choices_to_current_user,
        verbose_name=_('Network'),
    )
    rules_definition = models.TextField(_('Network Rule Definition'), blank=True,
                                        default=DEFAULT_RULE_DEFINITION)
    rules = models.TextField(_('Network Rules'), blank=True, default=DEFAULT_RULE)

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name=_('Owner')
    )

    organization = models.ForeignKey(
        Organizations,
        on_delete=models.SET_NULL,
        verbose_name=_('Organization'),
        null=True
    )

    created_at = models.DateTimeField(auto_now=False, auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True, auto_now_add=False)

    class Meta:
        db_table = 'network_rules'
        verbose_name = 'network rule'
        verbose_name_plural = 'network rules'

    def __str__(self):
        return '%s' % self.network

    def clean(self):

        filename_rule = '/tmp/net-rule-' + self.network.network_id + '.rules'
        file = open(filename_rule, 'w')
        file.write(self.rules_definition)
        file.close()

        shell = not settings.DEVELOPMENT
        print('SHELL', shell)

        command = '{} {} {}'.format(settings.NODEJS, settings.CLIJS, filename_rule)

        #result = subprocess.run([settings.NODEJS, settings.CLIJS, filename_rule],
        #                        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=False)
        result = subprocess.run(command,
                                stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=False)

        result_txt = result.stdout.decode('utf-8')

        print('RESULT', result_txt)
        if 'ERROR' in result_txt:
            error_msg = result_txt.split(':')
            #print(rules)
            raise ValidationError({'rules_definition': _('Syntax Error: ' + error_msg[1])})
        print(self.rules)
        os.remove(filename_rule)

    def save(self):
        self.user = self.network.user
        self.organization = self.network.organization

        filename_rule = '/tmp/net-rule-' + self.network.network_id + '.rules'
        #print('FILENAME ', filename_rule)
        file = open(filename_rule, 'w')
        file.write(self.rules_definition)
        file.close()

        shell = not settings.DEVELOPMENT

        if self.rules_definition is not None:
            print('FILENAME ', filename_rule)

            #result = subprocess.run([settings.NODEJS, settings.CLIJS, filename_rule],
            #                        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=shell)

            command = '{} {} {}'.format(settings.NODEJS, settings.CLIJS, filename_rule)

            result = subprocess.run(command,
                                    stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=False)
            self.rules = result.stdout.decode('utf-8')

        os.remove(filename_rule)
        return super(NetworkRules, self).save()
