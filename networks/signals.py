from django.contrib.auth.models import User
from .models import Networks, NetworkRoutes, Members
from controllers.models import Controllers, UserControllers
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
    try:
        ip_address(instance.ip_assignment)
        #print('It is come here')
        try:
            NetworkRoutes.objects.get(network=instance,
                                      ip_network=instance.ip_assignment,
                                      ip_netmask=instance.ip_assignment_netmask,
                                      gateway=None)
        except ObjectDoesNotExist:
            try:
                net_route = NetworkRoutes.objects.get(network=instance, gateway=None)
            except ObjectDoesNotExist:
                net_route = NetworkRoutes()

            net_route.network = instance
            net_route.ip_network = instance.ip_assignment
            net_route.ip_netmask = instance.ip_assignment_netmask
            net_route.save()
            #is_net_route = True

    except ValueError:
        try:
            net_route = NetworkRoutes.objects.get(network=instance, gateway=None)
            net_route.delete()
        except ObjectDoesNotExist:
            pass

    '''
    NetworkRoutes.objects.filter(network=instance).delete()
    '''
    '''
    for route in instance.route:
        ip_target = route['target'].split('/')
        via = route['via']
        try:
            NetworkRoutes.objects.get(network=instance,
                                      ip_network=ip_target[0],
                                      ip_netmask=ip_target[1],
                                      gateway=via)
        except ObjectDoesNotExist:
            net_route = NetworkRoutes(network=instance,
                                      ip_network=ip_target[0],
                                      ip_netmask=ip_target[1],
                                      gateway=via)
            net_route.save()
            
    '''
        

