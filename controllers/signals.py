from accounts.models import User
from controllers.models import Controllers
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.exceptions import ObjectDoesNotExist


@receiver(post_save, sender=User)
def assign_user_to_controller(sender, instance, created, **kwargs):
    if created:
        try:
            controller = Controllers.objects.get(id=1)
        except ObjectDoesNotExist:
            controller = Controllers()
            controller.name = 'Default Controller'
            controller.description = 'Default Initial Controller'
            controller.uri = 'http://localhost:9993'
            controller.token ='83hikjdna-change-me'
            controller.save()
