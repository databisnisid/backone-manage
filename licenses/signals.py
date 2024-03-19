from django.db.models.base import post_save
from django.dispatch import receiver
from licenses.models import Licenses
from networks.models import NetworkRules


@receiver(post_save, sender=Licenses)
def update_network_rules(sender, instance, created, **kwargs):
    if instance.get_license_status():
        network_rules = NetworkRules.objects.filter(
                        organization=instance.organization)

        for network_rule in network_rules:
            if network_rule.is_block_rule:
                network_rule.is_block_rule = False
                network_rule.save()

