from .models import Members, MemberPeers
from django.db.models.signals import post_delete
from django.dispatch import receiver


@receiver(post_delete, sender=Members)
def delete_member_peers(sender, instance, **kwargs):
    members = Members.objects.filter(member_id=instance.member_id).count()

    if members == 0:
        instance.peers.delete()
