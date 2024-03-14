from enum import unique
from django.core.validators import ValidationError
from django.db import models
from django.db.models.fields import b64encode
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from datetime import datetime
from uuid import getnode
from base64 import b64decode
from rsa import PrivateKey, decrypt
from config.utils import to_json, to_dictionary
import json
from accounts.models import Organizations
from crum import get_current_user


class Licenses(models.Model):
    def limit_choices_to_org():
        return { 'is_no_org': False }

    node_id = models.CharField(_('Node ID'), max_length=20, blank=True, null=True)
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
    get_organization_uuid.short_description = _('UUID')

    def get_controller_token(self):
        if self.organization:
            if self.organization.controller:
                token = self.organization.controller.token
                token_encode = b64encode(token.encode()).decode()
                return token_encode
            else:
                return None
        else:
            return None
    get_controller_token.short_description = _('Token')

    ''' Checking License '''
    def check_license(self):
        license_status = False
        license_status_msg = []
        license_valid_until = None
        if self.license_string:
            lic_decode = None
            lic_key_enc = None
            lic_key = None
            lic_decrypt = None
            lic_json = None

            try:
                lic_decode = b64decode(str(self.license_string))
            except:
                ''' License Code Decode Error '''
                license_status_msg.append('EC1105')


            if lic_decode:
                lic_key_enc = None
                lic_key = None
                lic_decrypt = None
                lic_json = None

                try:
                    lic_key_enc = b64decode(str(self.license_key))

                except:
                    ''' License Key Decode Error '''
                    license_status_msg.append('EC1107')

                if lic_key_enc:
                    try:
                        lic_key = PrivateKey.load_pkcs1(lic_key_enc)
                    except: 
                        ''' License Key Load Error '''
                        license_status_msg.append('EC1108')

                if lic_key:
                    try:
                        lic_decrypt = decrypt(lic_decode, lic_key).decode()
                        lic_json = to_json(lic_decrypt)
                    except:
                        ''' License Key Decrypt Error '''
                        license_status_msg.append('EC1109')

                #lic_key = PrivateKey.load_pkcs1(b64decode(str(self.license_key)))
                #lic_decrypt = decrypt(lic_decode, lic_key).decode()
                #lic_json = to_json(lic_decrypt)

                if lic_json:

                    node_id = ''
                    organization_uuid = ''
                    controller_token = ''

                    try:
                        node_id = lic_json['node_id']
                    except:
                        license_status_msg.append('EC1111')

                    ''' Check Node ID '''
                    ''' EC1101 - Node ID is not match '''
                    status_node_id = True
                    if node_id != self.node_id:
                        status_node_id = True
                        license_status_msg.append('EC1101')

                    try:
                        organization_uuid = lic_json['organization_uuid']
                    except:
                        license_status_msg.append('EC1112')

                    ''' Check Organiation UUID '''
                    ''' EC1102 - Organization UUID is not match '''
                    status_organization_uuid = True
                    if organization_uuid != str(self.get_organization_uuid()):
                        status_organization_uuid = False
                        license_status_msg.append('EC1102')

                    try:
                        controller_token = lic_json['controller_token']
                    except:
                        license_status_msg.append('EC1113')

                    ''' Check Token '''
                    ''' EC1103 - Token is not match '''
                    status_token = True
                    if controller_token != self.get_controller_token():
                        status_token = False
                        license_status_msg.append('EC1103')

                    if status_node_id and status_organization_uuid and status_token:
                        try:
                            valid_until = lic_json['valid_until']
                            ''' Check Validity '''
                            datetime_format = '%Y-%m-%d %H:%M:%S%z'
                            try:
                                license_valid_until = datetime.strptime(valid_until, datetime_format) 
                                current_time = timezone.now()

                                if license_valid_until >= current_time:
                                    license_status = True
                                    license_status_msg.append('VALID')
                                else:
                                    license_status_msg.append('EC1104')
                            except:
                                ''' Validity Error - Wrong date string '''
                                license_status_msg.append('EC1114')

                        except:
                            ''' Validity Error - No valid_until '''
                            license_status_msg.append('EC1114')
                            

                else:
                    ''' if lic_json '''
                    ''' JSON is None '''
                    license_status_msg.append('EC1106')


            #except ValueError:
            #    ''' License Key Error '''
            #    license_status_msg.append('EC1105')

        else:
            ''' Initial Create License, licenses key and code are empty'''
            license_status_msg.append('EC1100')

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

