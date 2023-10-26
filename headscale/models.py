from django.core.exceptions import ValidationError
from django.db import models
from django.forms.fields import validators
from django.utils.translation import gettext_lazy as _
from django.conf import settings
from django.core.validators import RegexValidator
from django.utils.html import format_html
from crum import get_current_user
from connectors.drivers.headscale import Headscale
from accounts.models import User, Organizations
from mqtt.models import Mqtt
from .utils import add_user, rename_user, delete_user, add_preauth_key


class HS_Users(models.Model):
    name_validator = RegexValidator("^[a-z0-9-.]*$")
    name = models.CharField(
            _('Name'), max_length=100,
            unique=True,
            validators=[name_validator],
            help_text=_('Lowercase ASCII letters numbers, hyphen and dots')
            )
    name_prev = models.CharField(_('Name Prev'), max_length=100)
    description = models.TextField(_('Description'), blank=True, null=True)

    created_at = models.DateTimeField(auto_now=False, auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True, auto_now_add=False)
    deleted_at = models.DateTimeField(blank=True, null=True)

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

    class Meta:
        managed = True
        db_table = 'hs_users'
        verbose_name = 'Network'
        verbose_name_plural = 'Networks'

    def __str__(self):
        return '{}'.format(self.name)

    def clean(self):
        if self.name.lower() == self.name_prev.lower():
            is_ok, result = add_user(self.name)
            if is_ok:
                self.id = result['id']
                self.created_at = result['createdAt']
            else:
                raise ValidationError(_('Error Response from Controller. Try again!'))
        else:
            is_ok, result = rename_user(self.name_prev, self.name)
            # Code to rename users
            if not is_ok:
                raise ValidationError(_('Error Response from Controller. Try again!'))

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        if self.user is None:
            self.user = get_current_user()

        #if self.organization is None:
        #    self.organization = self.user.organization

        self.name_prev = self.name

        return super(HS_Users, self).save(force_insert, force_update, using, update_fields)


class HS_Preauthkeys(models.Model):
    key = models.CharField(_('Key'), max_length=100)
    is_reusable = models.BooleanField(_('Reusable'), default=False)
    is_ephemeral = models.BooleanField(_('Ephemeral'), default=False)
    is_used = models.BooleanField(_('Used'), default=False)

    created_at = models.DateTimeField(auto_now=False, auto_now_add=True)
    expiration = models.DateTimeField()

    hs_user = models.ForeignKey(
            HS_Users, 
            on_delete=models.RESTRICT,
            verbose_name=_('Network')
            )

    organization = models.ForeignKey(
        Organizations,
        on_delete=models.SET_NULL,
        verbose_name=_('Organization'),
        null=True
    )

    class Meta:
        managed = True
        db_table = 'hs_preauthkeys'
        verbose_name = 'Auth Key'
        verbose_name_plural = 'Auth Keys'

    def __str__(self):
        return '{}'.format(self.key)

    def clean(self):
        is_ok, result = add_preauth_key(
                self.hs_user.name, 
                self.is_reusable,
                self.is_ephemeral,
                )

        if not is_ok:
            raise ValidationError(_('Error Response from Controller. Try again!'))
        else:
            self.id = result['id']
            self.key = result['key']
            self.expiration = result['expiration']
            self.created_at = result['createdAt']

    '''
    def save(self):
        self.organization = self.hs_user.organization
        super(HS_Preauthkeys, self).save()
    '''

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        self.organization = self.hs_user.organization
        return super(HS_Preauthkeys, self).save(force_insert, force_update, using, update_fields)


class HS_Nodes(models.Model):
    name = models.CharField(_('Name'), max_length=100)
    description = models.TextField(_('Description'), blank=True, null=True)

    machine_key = models.CharField(_('Machine Key'), max_length=100)
    node_key = models.CharField(_('Node Key'), max_length=100)
    disco_key = models.CharField(_('Disco Key'), max_length=100)
    hostname = models.CharField(_('Hostname'), max_length=50)
    given_name = models.CharField(_('Given Name'), max_length=100, unique=True)

    ipaddress_v4 = models.GenericIPAddressField(_('IP Address v4'))
    ipaddress_v6 = models.GenericIPAddressField(_('IP Address v6'))

    last_seen = models.DateTimeField(_('Last Seen'))
    last_update = models.DateTimeField(_('Last Update'), blank=True, null=True)
    expiry = models.DateTimeField(_('Expiry'))
    created_at = models.DateTimeField(auto_now=False, auto_now_add=True)

    is_online = models.BooleanField(_('Online'), default=False)

    hs_user = models.ForeignKey(
            HS_Users, 
            on_delete=models.RESTRICT,
            verbose_name=_('Network')
            )

    organization = models.ForeignKey(
        Organizations,
        on_delete=models.SET_NULL,
        verbose_name=_('Organization'),
        null=True
    )

    # Additional Fields
    address = models.CharField(max_length=250, blank=True, null=True)
    location = models.CharField(max_length=250, blank=True, null=True)
    online_at = models.DateField(_('Start Online'), blank=True, null=True)
    offline_at = models.DateTimeField(_('Stop Online'), blank=True, null=True)

    # Mobile
    mobile_regex = RegexValidator(regex=r'^62\d{9,15}$', message=_("Mobile number must be entered in the format: '628XXXXXXXXXXX'. Up to 15 digits allowed."))
    mobile_number_first = models.CharField(_('Mobile Number'), 
                                     validators=[mobile_regex], 
                                     max_length=20, blank=True, null=True)

    mqtt = models.ForeignKey(
        Mqtt,
        on_delete=models.SET_NULL,
        verbose_name=_('Mqtt'),
        null=True
    )

    class Meta:
        managed = True
        db_table = 'hs_nodes'
        verbose_name = 'Node'
        verbose_name_plural = 'Nodes'

    def __str__(self):
        return '{}'.format(self.name)

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        self.organization = self.hs_user.organization
        return super(HS_Nodes, self).save(force_insert, force_update, using, update_fields)

    def node_status(self):
        return format_html('<small>{}<br />{}<br />{}</small>'.format(self.ipaddress_v4, self.hs_user.name, self.online_status()))
    node_status.short_description = _('Status')

    def online_status(self):
        text = 'OFFLINE'
        color = 'red'
        if self.is_online:
            text = 'ONLINE'
            color = 'red'
        return format_html("<span style='color: {};'>{}</span>".format(color, text))

    def node_name_with_address(self):
        text = self.name
        if self.address:
            address_html = format_html(self.address.replace(',', '<br />'))
            text = format_html('{}<br /><small>{}</small>', self.name, address_html)
        return text
    node_name_with_address.short_description = _('Name and Address')


