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
