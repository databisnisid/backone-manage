from members.models import MemberPeers
from django.utils.timezone import localtime
from controllers.backend import Zerotier


print(localtime(), 'START - Synchronize Member Peers')
member_peers = MemberPeers.objects.all()

print(member_peers)
for member_peer in member_peers:
    print(member_peer)
    zt = Zerotier(member_peer.network.controller.uri, member_peer.network.controller.token)
    member_peer.peers = zt.get_member_peers(member_peer.member_id)
    print('Updating Member ' + member_peer.member_id)
    member_peer.save()
print(localtime(), 'DONE - Synchronize Member Peers')