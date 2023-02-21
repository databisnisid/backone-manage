from django.shortcuts import render
from qr_code.qrcode.utils import QRCodeOptions

def qr_code(request, network_id):
    # Build context for rendering QR codes.
    context = dict(
        qr_options=QRCodeOptions(size='h', border=1, error_correction='L'),
        network_id=network_id
    )

    # Render the view.
    return render(request, 'networks/qr_network_id.html', context=context)
