from .models import Members, MemberPeers
from django.db.models.signals import post_delete
from django.dispatch import receiver
from django.core.exceptions import ObjectDoesNotExist


@receiver(post_delete, sender=Members)
def delete_member_peers(sender, instance, **kwargs):
    members = Members.objects.filter(member_id=instance.member_id).count()

    if members == 0:
        try:
            MemberPeers.objects.get(member_id=instance.member_id).delete()
        #member_peers = MemberPeers.objects.filter(member_id=instance.member_id)
        except ObjectDoesNotExist:
            pass
        #for member_peer in member_peers:
        #    member_peer.delete()

        #instance.peers.delete()
