import uuid
from django.db import models
from django.utils.translation import gettext as _
from crum import get_current_user
from accounts.models import User, Organizations
from networks.models import Networks

# Create your models here.

class WebFilters(models.Model):
    name = models.CharField(_('Name'), max_length=50, unique=True)
    description = models.TextField(_('Description'), blank=True)
    uuid = models.UUIDField(editable=False, default=uuid.uuid4, unique=True)
    domains = models.TextField(_('Domain List'), help_text=_('List top domain to block'))

    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        verbose_name=_('User'),
        blank=True,
        null=True
    )

    organization = models.ForeignKey(
        Organizations,
        on_delete=models.SET_NULL,
        verbose_name=_('Organization'),
        blank=True,
        null=True
    )

    created_at = models.DateTimeField(auto_now=False, auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True, auto_now_add=False)


    class Meta:
        db_table = 'webfilter'
        verbose_name = 'Web Filter'
        verbose_name_plural = 'Web Filters'


    def __str__(self):
        return '{}'.format(self.name)

    def save(self):
        self.domains = self.domains.lower()
        current_user = get_current_user()
        if self.user is None:
            self.user = current_user

        if self.organization is None:
            self.organization = current_user.organization

        return super(WebFilters, self).save()

