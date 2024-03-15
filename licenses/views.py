from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.decorators import login_required
from django.db.models.fields import b64encode
from django.http import HttpResponse
#from django.shortcuts import render
#from wsgiref.util import FileWrapper
import json
from base64 import b64encode, b64decode
from django.http.response import JsonResponse
from django.views.decorators.csrf import requires_csrf_token
from .models import Licenses
from .utils import check_license


@login_required
def download_license(request, license_id):
    try:
        lic = Licenses.objects.get(id=license_id)
        token = lic.organization.controller.token
        token_encode = b64encode(token.encode()).decode()
        is_block_rule = 1 if lic.is_block_rule else 0
        lic_json = {
                'name': str(lic.organization.name),
                'node_id': str(lic.node_id),
                'uuid': str(lic.organization.uuid),
                'token': token_encode,
                'license_code': str(lic.license_string),
                'is_block_rule': is_block_rule
                }
    except ObjectDoesNotExist:
        lic_json = {}

    #print(lic_json)

    #filename = f"{context['title']}.json"
    try:
        #filename = lic_json['token'] + '.json'
        filename = lic_json['token'] + '.lic'
    except:
        filename = 'license.lic'
        #filename = 'lic.json'

    lic_json_str = json.dumps(lic_json)
    lic_json_enc = b64encode(lic_json_str.encode()).decode()
    #lic_json_enc = b64encode(lic_json_str.encode())

    #from io import StringIO
    #buffer = StringIO()
    #buffer.write(lic_json_enc)
    #print(lic_json_enc)

    response = HttpResponse(lic_json_enc, content_type='application/text')
    #response = HttpResponse(FileWrapper(buffer.getvalue()), content_type='application/zip')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    #json.dump(lic_json, response, indent=4)

    return response


@requires_csrf_token
def license_handler(request):
    is_ajax = request.META.get('HTTP_X_REQUESTED_WITH') == 'XMLHttpRequest'
    response_json = {
            'status': 0,
            'msg': 'Uknown Error'
            }
    if request.method == 'POST' and is_ajax:
        if request.body:
            print(request.body)
            lic_enc = request.body

            try:
                lic_json_str = b64decode(lic_enc).decode()

            except:
                lic_json_str = None

            if lic_json_str:
                #print(lic_json_str)
                lic_json = to_json(lic_json_str)
                if lic_json:
                    print(lic_json)
                    response_json = check_license(lic_json)
                else:
                    response_json['msg'] = 'License Code Error'

            else:
                response_json['msg'] = 'License Decode Error'
        else:
            response_json['msg'] = 'License is empty'

    response = JsonResponse(response_json)
    response.status_code = 200

    return response

