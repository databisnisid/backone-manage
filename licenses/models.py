from enum import unique
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from datetime import datetime
from uuid import getnode
from base64 import b64decode
from rsa import PrivateKey, decrypt
import json


class Licenses(models.Model):
    node_id = models.CharField(_('Node ID'), max_length=20, blank=True, null=True, unique=True)
    license_key = models.TextField(_('License Key'), blank=True, null=True)
    license_string = models.TextField(_('License String'), blank=True, null=True)


    created_at = models.DateTimeField(auto_now=False, auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True, auto_now_add=False)

    class Meta:
        db_table = 'licences'
        verbose_name = 'License'
        verbose_name_plural = 'Licenses'

    def __str__(self):
        return '%s' % self.node_id

    def save(self):
        ''' Get 12 first 12 characters (Docker supported) '''
        node_id = hex(getnode())[:12]
        if self.node_id is None or self.node_id != node_id:
            self.node_id = node_id

        return super(Licenses, self).save()

    def check_license(self):
        license_status = False
        if self.license_string:
            lic_decode = b64decode(self.license_string)
            lic_key = PrivateKey.load_pkcs1(self.license_key)
            lic_decrypt = decrypt(lic_decode, lic_key).decode()
            lic_json = json.load(lic_decrypt)
            datetime_format = '%Y-%m-%d %H:%M:%S.%f%z'
            lic_valid_until = datetime.strptime(lic_json['valid_until'], datetime_format) 

            if lic_valid_until >= timezone.now():
                license_status = True
            
        return license_status

