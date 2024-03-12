from enum import unique
from django.core.validators import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from datetime import datetime
from uuid import getnode
from base64 import b64decode
from rsa import PrivateKey, decrypt
from config.utils import to_json, to_dictionary
import json
from accounts.models import Organizations


class Licenses(models.Model):
    def limit_choices_to_org():
        return { 'is_no_org': False }

    node_id = models.CharField(_('Node ID'), max_length=20, blank=True, null=True, unique=True)
    license_key = models.TextField(_('License Key'), blank=True, null=True)
    license_string = models.TextField(_('License Code'), blank=True, null=True)

    organization = models.OneToOneField(
            Organizations,
            on_delete=models.SET_NULL,
            blank=True,
            null=True,
            verbose_name=('Organization'),
            limit_choices_to=limit_choices_to_org
            )

    created_at = models.DateTimeField(auto_now=False, auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True, auto_now_add=False)

    class Meta:
        db_table = 'licences'
        verbose_name = 'License'
        verbose_name_plural = 'Licenses'

    def __str__(self):
        return '%s' % self.node_id

    def clean(self):
        if self.organization is None:
            raise ValidationError({'organization': _('Organization must be filled')})

    def save(self):
        ''' Get 12 first 12 characters (Docker supported) '''
        node_id = hex(getnode())[:12]
        if self.node_id is None or self.node_id != node_id:
            self.node_id = node_id

        return super(Licenses, self).save()


    def get_organization_uuid(self):
        if self.organization:
            return self.organization.uuid
        else:
            return None
    get_organization_uuid.short_description = _('Organization UUID')

    ''' Checking License '''
    def check_license(self):
        license_status = False
        license_status_msg = []
        license_valid_until = None
        if self.license_string:
            lic_decode = b64decode(str(self.license_string))
            try:
                lic_key = PrivateKey.load_pkcs1(b64decode(str(self.license_key)))
                lic_decrypt = decrypt(lic_decode, lic_key).decode()
                lic_json = to_json(lic_decrypt)

                ''' Check Node ID '''
                ''' EC1101 - Node ID is no match '''
                status_node_id = True
                if lic_json['node_id'] != self.node_id:
                    status_node_id = True
                    license_status_msg.append('EC1101')

                ''' Check Organiation UUID '''
                ''' EC1102 - Organization UUID is no match '''
                status_organization_uuid = True
                if lic_json['organization_uuid'] != self.get_organization_uuid():
                    status_organization_uuid = False
                    license_status_msg.append('EC1102')

                if status_node_id and status_organization_uuid:
                    ''' Check Validity '''
                    datetime_format = '%Y-%m-%d %H:%M:%S%z'
                    license_valid_until = datetime.strptime(lic_json['valid_until'], datetime_format) 
                    current_time = timezone.now()

                    if license_valid_until >= current_time:
                        license_status = True
                        license_status_msg.append('VALID')
                    else:
                        license_status_msg.append('EC1104')


            except ValueError:
                pass

        license_msg = '; '.join(license_status_msg)
            
        return license_status, license_valid_until, license_msg

    def get_license_time(self):
        lic_status, lic_time, lic_msg = self.check_license()
        return lic_time
    get_license_time.short_description = _('Valid Until')

    def get_license_msg(self):
        lic_status, lic_time, lic_msg = self.check_license()
        return lic_msg
    get_license_msg.short_description = _('License Status')

