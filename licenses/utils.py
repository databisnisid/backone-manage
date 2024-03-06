from django.core.exceptions import ObjectDoesNotExist
from django.conf import settings
from rsa import PublicKey, encrypt
from uuid import getnode
from base64 import b64encode
from .models import Licenses


def encrypt_node_id(key):
    node_id = hex(getnode())
    node_id_encrypted = encrypt(node_id(),encode(), publick_key)
    node_id_b64 = b64encode(node_id_encrypted).decode()
    return node_id_b64


def check_license():
    try:
        license_key_pem = Licenses.objects.get(id=1)
    except ObjectDoesNotExist
        license_key_pem = None

    try:
        public_key = PublicKey.load_pkcs1(license_key_pem)
    except ValueError:
        public_key = None

    if public_key:
        node_id = encrypt_node_id(publick_key)






