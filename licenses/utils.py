from django.core.exceptions import ObjectDoesNotExist
from django.conf import settings
from django.utils.timezone import datetime
from django.utils import timezone
from rsa import PublicKey, encrypt
from uuid import getnode
from base64 import b64decode, b64encode

from accounts.models import Organizations
from controllers.models import Controllers
from networks.models import NetworkRules
from .models import Licenses


''' Not Used '''
def encrypt_node_id(key):
    node_id = hex(getnode())
    node_id_encrypted = encrypt(node_id(),encode(), publick_key)
    node_id_b64 = b64encode(node_id_encrypted).decode()
    return node_id_b64


''' Check License Validity True/False'''
def is_license_valid(user):

    result = False

    if not user.organization.is_no_org:
        try:
            lic = Licenses.objects.get(organization=user.organization)
            lic_status, lic_valid_until, lic_msg = lic.check_license()

            if lic_status:
                result = True

        except ObjectDoesNotExist:
            pass

    return result


def check_license(lic_json):
    node_id = lic_json['node_id']
    uuid = lic_json['uuid']
    token = b64decode(lic_json['token']).decode()
    license_code = lic_json['license_code']
    is_block_rule = lic_json['is_block_rule']

    try:
        valid_until = lic_json['valid_until']
    except KeyError:
        valid_until = str(timezone.now())

    lic_result = {
            'status': 0,
            'msg': 'License is NOT VALID'
            }
    try:
        controller = Controllers.objects.get(token=token)
    except ObjectDoesNotExist:
        controller = None

    lic = None
        
    if controller:
        try:
            organization = Organizations.objects.get(uuid=uuid,
                                                    controller=controller)
        except ObjectDoesNotExist:
            organization = None

        if organization:
            try:
                lic = Licenses.objects.get(node_id=node_id,
                                   organization=organization)
            except ObjectDoesNotExist:
                lic_result['msg'] = 'License is NOT FOUND! Check Node ID'


    datetime_format = '%Y-%m-%d %H:%M:%S%z'
    try:
        new_license_valid_until = datetime.strptime(valid_until, datetime_format)
    except:
        new_license_valid_until = None

    if new_license_valid_until:
        if lic:
            lic_status, lic_valid_until, lic_msg = lic.check_license()

            if new_license_valid_until > timezone.now():
                if lic_valid_until:
                    if new_license_valid_until > lic_valid_until:
                        lic.license_string = license_code
                        lic.is_block_rule = is_block_rule
                        lic.save()
                        lic_result['status'] = 1
                        lic_result['msg'] = 'License Update is succeed'
                    else:
                        lic_result['msg'] = 'New license validity is older than installed license'
                else:
                    try:
                        license_key = lic_json['license_key']
                        lic.license_key = license_key
                        lic.license_string = license_code
                        lic.is_block_rule = is_block_rule
                        lic.save()
                        lic_result['status'] = 1
                        lic_result['msg'] = 'License Init is succeed'
                    except:
                        lic_result['msg'] = 'Init License is required' 

            else:
                lic_result['msg'] = 'License validity must be in the future'

        else:
            lic_result['msg'] = 'License is NOT Match'

    else:
        ''' if new_license_valid_until: '''
        lic_result['msg'] = 'License Validity is INVALID'
        

    return lic_result


''' Preparation for Block Rule base on License '''
''' Running every midnite in cronjob '''
def check_license_status():
    licenses = Licenses.objects.all()

    for license in licenses:
        if license.is_block_rule:

            is_block_rule = True
            ''' License status True - VALID '''
            if license.get_license_status():
                is_block_rule = False

            network_rules = NetworkRules.objects.filter(
                            organization=license.organization)

            for network_rule in network_rules:
                if network_rule.is_block_rule != is_block_rule:
                    network_rule.is_block_rule = is_block_rule
                    network_rule.save()

