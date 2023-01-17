from controllers.workers import zt_import_members
from django.core.exceptions import ObjectDoesNotExist
from networks.models import Networks, NetworkRoutes


def import_members_for_network(network_id):
    try:
        network = Networks.objects.get(network_id=network_id)
        zt_import_members(network)

    except ObjectDoesNotExist:
        pass
