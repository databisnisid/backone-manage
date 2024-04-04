from django.db.models import ObjectDoesNotExist
from django.shortcuts import render
from qr_code.qrcode.utils import QRCodeOptions
from django.core.serializers import serialize
from django.http import HttpResponse, JsonResponse
from members.models import Members
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


def network_ping_stats(request, network_id):
    packet_loss_array = []
    round_trip_array = []
    packet_loss_avg = 100
    round_trip_avg = 1000

    try:
        network = Networks.objects.get(network_id=network_id)

        members = Members.objects.filter(
                peers__isnull=False,
                network=network)

        for member in members:
            if member.is_online():
                packet_loss = member.packet_loss()
                round_trip = member.round_trip()

                if packet_loss >= 0 and round_trip >= 0:
                    packet_loss_array.append(packet_loss)
                    round_trip_array.append(round_trip)

    except ObjectDoesNotExist:
        network = None

    if network and packet_loss_array and round_trip_array:
        packet_loss_avg = sum(packet_loss_array) / len(packet_loss_array)
        round_trip_avg = sum(round_trip_array) / len(round_trip_array)

        data = {
                'network_name': network.name,
                'packet_loss': packet_loss_avg,
                'round_trip': round_trip_avg,
                'num_sample': len(packet_loss_array)
            }

    else:
        data = {
                'status': False
                }

    #print(data)
    return JsonResponse(data)


