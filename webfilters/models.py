from enum import unique
import uuid
from django.db import models
from django.core.exceptions import MultipleObjectsReturned, ObjectDoesNotExist, ValidationError
from django.utils.translation import gettext as _
from crum import get_current_user
from accounts.models import User, Organizations
from networks.models import Networks
from members.models import Members

# Create your models here.

class WebFiltersOrg(models.Model):
    organization = models.OneToOneField(
        Organizations,
        on_delete=models.RESTRICT,
        verbose_name=_('Organization'),
    )

    network = models.ForeignKey(
        Networks,
        on_delete=models.RESTRICT,
        verbose_name=_('Network'),
    )

    created_at = models.DateTimeField(auto_now=False, auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True, auto_now_add=False)

    
    class Meta:
        db_table = 'webfilter_org'
        verbose_name = 'Web Filter Network '
        verbose_name_plural = 'Web Filters Network '

    def __str__(self):
        return '{}'.format(self.organization)


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

    network = models.ForeignKey(
        Networks,
        on_delete=models.SET_NULL,
        verbose_name=_('Network'),
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

    def clean(self):
        current_user = get_current_user()
        
        if not current_user.is_superuser:
            try:
                network = WebFiltersOrg.objects.get(organization=current_user.organization)
                self.network = network.network

            except ObjectDoesNotExist or MultipleObjectsReturned:
                if current_user.organization.features.is_webfilter and not current_user.organization.features.is_webfilter_multinet:
                    raise ValidationError(_('Please setup Org<->Net correlation. Contact Administrator!'))
                else:
                    pass

    def save(self):
        self.domains = self.domains.lower()
        current_user = get_current_user()
        if self.user is None:
            self.user = current_user

        if self.organization is None:
            self.organization = current_user.organization

        return super(WebFilters, self).save()


class WebFiltersMembers(models.Model):
    def limit_choices_to_current_user():
        current_user = get_current_user()
        if not current_user.is_superuser:
            if current_user.organization.features.is_webfilter and not current_user.organization.features.is_webfilter_multinet:
                try:
                    network = WebFiltersOrg.objects.get(organization=current_user.organization)
                    return {'network': network.network }

                except ObjectDoesNotExist or MultipleObjectsReturned:
                    return {'organization': current_user.organization}
            else:
                return {'organization': current_user.organization}

        else:
            return {}

    member = models.OneToOneField(
            Members,
            on_delete=models.CASCADE,
            limit_choices_to=limit_choices_to_current_user,
            verbose_name=_('Member'),

            )

    webfilter = models.ForeignKey(
            WebFilters,
            on_delete=models.CASCADE,
            limit_choices_to=limit_choices_to_current_user,
            verbose_name=_('WebFilter'),
            )

    class Meta:
        db_table = 'webfilter_member'
        verbose_name = _('WebFilter Member')
        verbose_name_plural = _('WebFilter Members')


    def __str__(self):
        return '{}'.format(self.member)

