from unittest import mock

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from accounts.models import Features, Organizations
from controllers.models import Controllers
from members.models import Members
from networks.models import Networks
from problems.models import MemberProblems
from monitor.models import MonitorRules

User = get_user_model()

FAKE_STATUS = {"address": "fake00000000"}
FAKE_MEMBER = {"status": 1, "authorized": True}
FAKE_PEERS = {"address": "peer1", "paths": [{"address": "10.0.0.1"}]}
FAKE_NETWORK = {
    "nwid": "nwid_1",
    "name": "net",
    "routes": [{"target": "10.0.0.0/24", "via": None}],
}


class AppApiMultiTenancyTests(TestCase):
    """T20: non-superuser sees own org only; superuser sees union."""

    @classmethod
    def setUpTestData(cls):
        cls.features = Features.objects.create(name="Default", number_of_member=100)

        def make_org(name):
            with mock.patch.object(Controllers, "save", autospec=True):
                org = Organizations(name=name, features=cls.features)
                org.save()
            return org

        cls.org_a = make_org("OrgA")
        cls.org_b = make_org("OrgB")
        # is_no_org org for user-scoped branch
        cls.org_no = make_org("OrgNo")
        cls.org_no.is_no_org = True
        cls.org_no.save()

        with mock.patch("controllers.backend.Zerotier.status", return_value=FAKE_STATUS):
            cls.controller = Controllers(
                name="ctl", uri="http://controller:9993", token="tok"
            )
            cls.controller.save()

        cls.admin = User.objects.create_superuser(
            username="admin", email="admin@t.co", password="x"
        )
        cls.u_a = User.objects.create_user(
            username="ua", email="ua@t.co", password="x", organization=cls.org_a
        )
        cls.u_b = User.objects.create_user(
            username="ub", email="ub@t.co", password="x", organization=cls.org_b
        )
        cls.u_no = User.objects.create_user(
            username="uno", email="uno@t.co", password="x", organization=cls.org_no
        )
        cls.u_out = User.objects.create_user(
            username="out", email="out@t.co", password="x"
        )  # no org

    def make_net(self, name, org, owner, count):
        with mock.patch.object(
            Controllers, "save", autospec=True
        ), mock.patch(
            "networks.models.Zerotier"
        ) as zt_cls:
            zt = zt_cls.return_value
            zt.list_networks.return_value = []
            zt.add_network.return_value = dict(FAKE_NETWORK, nwid=f"nwid_{name}")
            zt.get_network_info.return_value = FAKE_NETWORK
            zt.set_network.return_value = FAKE_NETWORK
            net = Networks(
                name=name,
                controller=self.controller,
                organization=org,
                user=owner,
                network_id=f"nwid_{name}",
            )
            net.save()
            return net

    def make_member(self, member_id, name, net, count):
        with mock.patch.object(
            Controllers, "save", autospec=True
        ), mock.patch("members.models.Zerotier") as zt_cls:
            zt = zt_cls.return_value
            zt.set_member.return_value = FAKE_MEMBER
            zt.get_member_peers.return_value = FAKE_PEERS
            member = Members(
                name=name,
                member_id=member_id,
                network=net,
                ipaddress="10.0.0.1",
            )
            member.save()
            member.mqtt = None
            member.save_base(raw=False)
            return member

    def test_org_scope(self):
        net_a = self.make_net("A", self.org_a, self.u_a, 2)
        net_b = self.make_net("B", self.org_b, self.u_b, 2)
        self.make_member("node-a1", "Node A1", net_a, 1)
        self.make_member("node-a2", "Node A2", net_a, 2)
        self.make_member("node-b1", "Node B1", net_b, 1)

        self.client.force_login(self.u_a)
        r = self.client.get(reverse("app_members"))
        self.assertEqual(r.status_code, 200)
        ids_a = {m["member_id"] for m in r.json()}
        self.assertEqual(ids_a, {"node-a1", "node-a2"})

        self.client.force_login(self.u_b)
        r = self.client.get(reverse("app_members"))
        ids_b = {m["member_id"] for m in r.json()}
        self.assertEqual(ids_b, {"node-b1"})

        # Disjoint
        self.assertTrue(ids_a.isdisjoint(ids_b))

    def test_superuser_sees_union(self):
        net_a = self.make_net("A", self.org_a, self.u_a, 2)
        net_b = self.make_net("B", self.org_b, self.u_b, 2)
        self.make_member("node-a1", "Node A1", net_a, 1)
        self.make_member("node-b1", "Node B1", net_b, 1)

        self.client.force_login(self.u_a)
        r = self.client.get(reverse("app_members"))
        ids_a = {m["member_id"] for m in r.json()}

        self.client.force_login(self.admin)
        r = self.client.get(reverse("app_members"))
        ids_super = {m["member_id"] for m in r.json()}
        self.assertEqual(ids_super, {"node-a1", "node-b1"})
        self.assertTrue(ids_a.issubset(ids_super))

    def test_no_org_user_scoped(self):
        net_a = self.make_net("A", self.org_a, self.u_a, 2)
        self.make_member("node-a1", "Node A1", net_a, 1)

        self.client.force_login(self.u_no)
        r = self.client.get(reverse("app_members"))
        self.assertEqual(r.json(), [])

    def test_telemetry_404_for_other_org(self):
        net_a = self.make_net("A", self.org_a, self.u_a, 2)
        self.make_member("node-a1", "Node A1", net_a, 1)

        self.client.force_login(self.u_b)
        r = self.client.get(
            reverse("app_member_telemetry", args=["node-a1"])
        )
        self.assertEqual(r.status_code, 404)

    def test_summary_networks_scoped(self):
        self.make_net("A", self.org_a, self.u_a, 2)
        self.make_net("B", self.org_b, self.u_b, 2)

        self.client.force_login(self.u_a)
        r = self.client.get(reverse("app_summary"))
        self.assertEqual(r.status_code, 200)
        data = r.json()
        self.assertEqual(data["networks"], 1)
        self.assertEqual(data["members"], 0)

    def test_me_requires_login(self):
        r = self.client.get(reverse("app_me"))
        self.assertEqual(r.status_code, 302)  # redirect to login

    def test_problems_scoped(self):
        net_a = self.make_net("A", self.org_a, self.u_a, 2)
        member = self.make_member("node-a1", "Node A1", net_a, 1)
        rule = MonitorRules(name="High CPU", organization=self.org_a, user=self.u_a)
        rule.save()
        MemberProblems(member=member, problem=rule).save()

        self.client.force_login(self.u_a)
        r = self.client.get(reverse("app_problems"))
        data = r.json()
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["member"]["member_id"], "node-a1")

        self.client.force_login(self.u_b)
        r = self.client.get(reverse("app_problems"))
        self.assertEqual(r.json(), [])