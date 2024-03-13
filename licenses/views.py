from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpResponse
from django.shortcuts import render
import json
from .models import Licenses


def json_download(request, license_id):
    try:
        lic = Licenses.objects.get(id=license_id)
        lic_json = {
                'node_id': str(lic.node_id),
                'uuid': str(lic.organization.uuid),
                'token': str(lic.organization.controller.token),
                'license_code': str(lic.license_string)
                }
    except ObjectDoesNotExist:
        lic_json = {}

    print(lic_json)

    #filename = f"{context['title']}.json"
    filename = 'lic.json'
    response = HttpResponse(content_type='application/json')
    json.dump(lic_json, response, indent=4)

    return response

