from controllers.models import Controllers #, UserControllers
from .models import Organizations, Features, User
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.exceptions import ObjectDoesNotExist


@receiver(post_save, sender=User)
def first_assign_user_to_default_organization(sender, instance, created, **kwargs):
    #if created and instance.organization is None:
    if created:
        if instance.organization is None:
            try:
                org = Organizations.objects.get(id=1)

            except ObjectDoesNotExist:
                try:
                    controller = Controllers.objects.get(id=1)
                except ObjectDoesNotExist:
                    controller = Controllers()
                    controller.name = 'Default Controller'
                    controller.description = 'Default Initial Controller'
                    controller.uri = 'http://localhost:9993'
                    controller.token = '83hikjdna-change-me'
                    controller.save()

                try:
                    features = Features.objects.get(id=1)

                except ObjectDoesNotExist:
                    features = Features()
                    features.name = 'BasicFeatures'
                    features.description = 'Basic Features'
                    features.save()

                org = Organizations()
                org.name = 'NoOrg'
                org.is_no_org = True
                org.controller = controller
                org.features = features
                org.save()

            instance.organization = org
            instance.save()
