from django.shortcuts import render
from qr_code.qrcode.utils import QRCodeOptions
from django.core.serializers import serialize
from django.http import HttpResponse
from .models import Networks


def qr_code(request, network_id):
    # Build context for rendering QR codes.
    context = dict(
        qr_options=QRCodeOptions(size='h', border=1, error_correction='L'),
        network_id=network_id
    )

    # Render the view.
    return render(request, 'networks/qr_network_id.html', context=context)


def networks_list_json(request):
    network = Networks.objects.all()
    data = serialize(
            "json", network, fields=('id', 'name', 'description', 'network_id')
            )
    return HttpResponse(data, content_type="application/json")



