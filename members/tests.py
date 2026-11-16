from unittest import mock

from django.core.exceptions import ValidationError
from django.test import TestCase

from accounts.models import User, Organizations
from controllers.models import Controllers
from networks.models import Networks
from members import models as members_models
from members.models import Members


class MembersZeroTierSaveTests(TestCase):
    """V1 / V9: Members.save() must surface a ZeroTier controller failure to the
    user (ValidationError) and NOT persist a local row that diverges from the
    controller. Zerotier.query() returns {'status':0} on network failure."""

    def setUp(self):
        self.user = User.objects.create_user(username="t2user", password="x")
        self.org = Organizations(name="testorg", uuid="12345678-1234-1234-1234-123456789012", is_no_org=False)
        Organizations.objects.bulk_create([self.org])
        self.controller = Controllers(name="testctrl", uri="http://localhost:9999", token="testtoken123")
        Controllers.objects.bulk_create([self.controller])
        self.network = Networks(name="testnet", network_id="net-1",
                                user=self.user, organization=self.org, controller=self.controller)
        Networks.objects.bulk_create([self.network])

    @mock.patch.object(members_models.Zerotier, "set_member", return_value={"status": 0})
    def test_save_raises_on_controller_failure(self, mock_set):
        m = Members(name="m", member_id="abcdefghij", network=self.network,
                    is_authorized=True)
        with self.assertRaises(ValidationError):
            m.save()
        self.assertFalse(Members.objects.filter(member_id="abcdefghij").exists())

    @mock.patch.object(members_models.Zerotier, "set_member", return_value={"id": "x"})
    @mock.patch.object(members_models.Zerotier, "get_member_peers", return_value={"status": 0})
    def test_save_raises_on_peers_failure(self, mock_peers, mock_set):
        m = Members(name="m", member_id="abcdefghij", network=self.network,
                    is_authorized=True)
        with self.assertRaises(ValidationError):
            m.save()
        self.assertFalse(Members.objects.filter(member_id="abcdefghij").exists())

    @mock.patch.object(members_models.Zerotier, "set_member", return_value={"id": "x"})
    @mock.patch.object(members_models.Zerotier, "get_member_peers", return_value={"paths": [{"address": "1.2.3.4"}]})
    def test_save_persists_on_success(self, mock_peers, mock_set):
        m = Members(name="m", member_id="abcdefghij", network=self.network,
                    is_authorized=True)
        m.save()
        self.assertTrue(Members.objects.filter(member_id="abcdefghij").exists())

    @mock.patch.object(members_models.Zerotier, "set_member", return_value={"id": "x"})
    @mock.patch.object(members_models.Zerotier, "get_member_peers",
                       return_value={"address": "abcdefghij", "paths": [{"address": "1.2.3.4"}]})
    def test_save_links_peers_fk(self, mock_peers, mock_set):
        """A saved member must point at its MemberPeers row; with a NULL FK
        is_online() can only read offline."""
        m = Members(name="m", member_id="abcdefghij", network=self.network,
                    is_authorized=True, ipaddress="10.0.0.1")
        m.save()
        m.refresh_from_db()
        self.assertIsNotNone(m.peers_id)
        self.assertEqual(m.peers.member_id, "abcdefghij")

    def test_is_online_without_peers_data(self):
        """No redis entry and no FK must read offline, not raise."""
        m = Members(member_id="nosuchmember")
        self.assertFalse(m.is_online())

class MembersPeerStatusTests(TestCase):
    """Member Status and BackOne Online must agree, and must never report
    OFFLINE just because Members.peers points at a stale/foreign row."""

    def setUp(self):
        # Keep the rendering path off live Redis (ipaddress_ts, ipinfo lookups).
        for patcher in (
            mock.patch.object(members_models, "get_msg_by_index", return_value=""),
            mock.patch.object(members_models.redis_ipinfo, "get_as_name", return_value=""),
        ):
            patcher.start()
            self.addCleanup(patcher.stop)
        self.user = User.objects.create_user(username="t3user", password="x")
        self.org = Organizations(name="t3org", uuid="12345678-1234-1234-1234-123456789012", is_no_org=False)
        Organizations.objects.bulk_create([self.org])
        self.controller = Controllers(name="t3ctrl", uri="http://localhost:9999", token="testtoken123")
        Controllers.objects.bulk_create([self.controller])
        self.network = Networks(name="t3net", network_id="net-3",
                                user=self.user, organization=self.org, controller=self.controller)
        Networks.objects.bulk_create([self.network])

    def _member(self, member_id="e3071f023f", peers=None):
        m = Members(name="m", member_id=member_id, network=self.network,
                    ipaddress="192.168.23.1", is_authorized=True)
        Members.objects.bulk_create([m])
        m = Members.objects.get(member_id=member_id)
        if peers is not None:
            Members.objects.filter(pk=m.pk).update(peers=peers)
            m.refresh_from_db()
        return m

    def _row(self, member_id, peers, network=None):
        row = members_models.MemberPeers(member_id=member_id, peers=str(peers),
                                        network=network or self.network)
        row.save_base(raw=False)
        return row

    @mock.patch.object(members_models, "get_member_peers_from_redis",
                       return_value={"paths": [{"address": "180.244.1.55/24064"}],
                                     "version": "1.14.1", "latency": 33})
    def test_status_online_when_fk_row_is_empty(self, mock_redis):
        stale = self._row("c2f8017a60", {})
        m = self._member(peers=stale)
        self.assertTrue(m.is_online())
        self.assertIn("DIRECT", str(m.member_status()))
        self.assertIn("180.244.1.55", str(m.list_peers()))

    @mock.patch.object(members_models, "get_member_peers_from_redis", return_value={})
    def test_status_offline_when_no_live_peers(self, mock_redis):
        m = self._member(peers=self._row("e3071f023f", {}))
        self.assertFalse(m.is_online())
        self.assertIn("OFFLINE", str(m.member_status()))

    @mock.patch.object(members_models, "get_member_peers_from_redis", return_value={})
    @mock.patch.object(members_models.Zerotier, "set_member", return_value={"id": "x"})
    @mock.patch.object(members_models.Zerotier, "get_member_peers",
                       return_value={"paths": [{"address": "10.0.0.1/9993"}],
                                     "version": "1.14.1", "latency": 12})
    def test_save_relinks_fk_to_own_row(self, mock_peers, mock_set, mock_redis):
        foreign = self._row("0123456789", {}, network=self.network)
        m = self._member(member_id="abcdefghij", peers=foreign)
        m.name = "renamed"
        m.save()
        m.refresh_from_db()
        self.assertEqual(m.peers.member_id, "abcdefghij")
        self.assertEqual(m.peers.network_id, self.network.id)
        self.assertTrue(m.is_online())
