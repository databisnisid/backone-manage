from django.contrib.auth.models import User
from .models import Networks, NetworkRoutes
from members.models import Members
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.exceptions import ObjectDoesNotExist
from ipaddress import ip_address
from config.utils import to_dictionary


@receiver(post_save, sender=Networks)
def update_members(sender, instance, created, **kwargs):
    Members.objects.filter(network=instance).update(user=instance.user)
    NetworkRoutes.objects.filter(network=instance).update(user=instance.user)


@receiver(post_save, sender=Networks)
def first_network_route(sender, instance, created, **kwargs):
    NetworkRoutes.objects.filter(network=instance, gateway=None).delete()

    if instance.ip_address_networks is not None:
        print('Add Routing', instance.ip_address_networks)
        ip_address_list = instance.ip_address_networks.split(',')
        for ip_address_network in ip_address_list:
            try:
                NetworkRoutes.objects.get(network=instance, ip_network=ip_address_network, gateway=None)
            except ObjectDoesNotExist:
                net_route = NetworkRoutes()
                net_route.network = instance
                net_route.ip_network = ip_address_network
                net_route.save()

