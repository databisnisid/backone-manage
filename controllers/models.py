from django.db import models
from django.contrib.auth.models import User
from .backend import Zerotier
from config.utils import to_dictionary
from django.utils.translation import gettext as _
from django.utils.html import format_html


class Controllers(models.Model):
    name = models.CharField(_('Name'), max_length=50, default='Default Controller')
    description = models.TextField(_('Description'), blank=True)
    uri = models.URLField(_('URL'), max_length=100, default='http://localhost:9993', unique=True)
    token = models.CharField(_('Token'), max_length=50, unique=True)
    #node_id = models.CharField(_('Node ID'), max_length=20, blank=True)

    configuration = models.TextField(_('Configuration'), blank=True)

    created_at = models.DateTimeField(auto_now=False, auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True, auto_now_add=False)

    class Meta:
        db_table = 'controllers'
        verbose_name = 'controller'
        verbose_name_plural = 'controllers'

    def __str__(self):
        return '%s' % self.name

    def save(self):
        zt = Zerotier(self.uri, self.token)
        #self.node_id = zt.get_node_id()
        self.configuration = zt.status()

        return super(Controllers, self).save()

    def status(self):
        config = to_dictionary(self.configuration)
        if config['online']:
            return format_html("<span style='color: green;'>ONLINE</span>")
        else:
            return format_html("<span style='color: red;'>OFFLINE</span>")

    status.short_description = _('Status')

    def node_id(self):
        config = to_dictionary(self.configuration)
        if 'address' in config:
            return config['address']
        else:
            return ''
    node_id.short_description = _('Node ID')

    def version(self):
        config = to_dictionary(self.configuration)
        if 'version' in config:
            return config['version']
        else:
            return ''
    version.short_description = _('Version')


class UserControllers(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
    )
    controller = models.ForeignKey(
        Controllers,
        on_delete=models.CASCADE,
        verbose_name=_('Controller')
    )

    class Meta:
        db_table = 'user_controller'
        verbose_name = 'user Controller'
        verbose_name_plural = 'user Controllers'

    def __str__(self):
        return '%s' % self.user
