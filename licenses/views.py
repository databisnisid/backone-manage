from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpResponse
from django.shortcuts import render
from .models import Licenses


def json_download(request, license_id):
    try:
        lic = Licenses.objects.get(id=license_id)
        lic_json = {
                'node_id': lic.node_id,
                'uuid': lic.organization.uuid,
                'token': lic.organization.controller.token,
                'license_code': lic.license_string
                }
    except ObjectDoesNotExist:
        lic_json = {}

    return HttpResponse(lic_json, 
                        content_type='application/json',
                        mimetype='application/force-download')

