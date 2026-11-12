import json
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
 
    def _put_net(self, net, payload):
        url = reverse("app_network_update", args=[net.network_id])
        return self.client.put(
            url, data=json.dumps(payload), content_type="application/json"
        )

    def test_ip_allocation_change_rejected(self):
        """PUT with a different ip_allocation -> 400, DB value untouched."""
        net = self.make_net("C", self.org_a, self.u_a, 1)
        Networks.objects.filter(pk=net.pk).update(
            ip_address_networks="10.0.0.0/24"
        )
        self.client.force_login(self.admin)

        r = self._put_net(
            net, {"name": "C", "ip_allocation": "192.168.1.0/24"}
        )
        self.assertEqual(r.status_code, 400)
        self.assertIn("ip_allocation", r.json()["error"])
        net.refresh_from_db()
        self.assertEqual(net.ip_address_networks, "10.0.0.0/24")

    def test_ip_allocation_unchanged_accepted(self):
        """PUT echoing the current ip_allocation passes the immutability guard."""
        net = self.make_net("D", self.org_a, self.u_a, 1)
        Networks.objects.filter(pk=net.pk).update(
            ip_address_networks="10.0.0.0/24"
        )
        # mirror production data: org linked to controller, and
        # Networks.clean() requires controller.configuration["address"]
        # to equal network_id[:10]
        Organizations.objects.filter(pk=self.org_a.pk).update(
            controller=self.controller
        )
        Controllers.objects.filter(pk=self.controller.pk).update(
            configuration='{"address": "%s"}' % net.network_id[:10]
        )

        self.client.force_login(self.admin)

        with mock.patch("networks.models.Zerotier") as zt_cls:
            zt_cls.return_value.list_networks.return_value = []
            zt_cls.return_value.get_network_info.return_value = FAKE_NETWORK
            zt_cls.return_value.set_network.return_value = FAKE_NETWORK
            r = self._put_net(net, {"name": "D", "ip_allocation": "10.0.0.0/24"})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()["ip_allocation"], "10.0.0.0/24")


class AccessLogApiTests(TestCase):
    """T16: axes access history endpoint — V26, V27, V29, V30, V31."""

    @classmethod
    def setUpTestData(cls):
        from axes.models import AccessLog, AccessFailureLog

        cls.features = Features.objects.create(name="F", number_of_member=10)

        def make_org(name, no_org=False):
            org = Organizations(name=name, features=cls.features, is_no_org=no_org)
            org.save()
            return org

        cls.org_a = make_org("A")
        cls.org_b = make_org("B")
        cls.org_no = make_org("NoOrgA", no_org=True)

        # accounts/signals.py:9 assigns org id=1 to any user created without an org,
        # so a NULL-org user cannot be fabricated here — the "no org" branch is
        # covered by the is_no_org user instead.
        cls.admin = User.objects.create_superuser("root", "r@t.co", "x")
        cls.u_a = User.objects.create_user("ua", "a@t.co", "x", organization=cls.org_a)
        cls.u_a2 = User.objects.create_user("ua2", "a2@t.co", "x", organization=cls.org_a)
        cls.u_b = User.objects.create_user("ub", "b@t.co", "x", organization=cls.org_b)
        cls.u_no = User.objects.create_user("uno", "n@t.co", "x", organization=cls.org_no)

        # Out-of-order insert order: ordering must come from attempt_time, not PK.
        for username in ("ub", "ua", "uno"):
            AccessLog.objects.create(
                username=username, ip_address="10.0.0.1", user_agent="ua",
                http_accept="*", path_info="/accounts/login/1:abc:def:secret-token",
            )
        AccessFailureLog.objects.create(
            username="ua", ip_address="10.0.0.2", user_agent="ua",
            http_accept="*", path_info="/login/", locked_out=True,
        )
        AccessFailureLog.objects.create(
            username="ghost", ip_address="10.0.0.3", user_agent="ua",
            http_accept="*", path_info="/login/", locked_out=False,
        )

    def get(self, user):
        # force_login fires axes user_logged_in, which writes an AccessLog row for
        # the actor — snapshot after login so assertions see only fixture rows.
        self.client.force_login(user)
        return self.client.get(reverse("app_access_logs"))

    def test_flag_enabled(self):
        """V28: the failure log must actually be written."""
        from django.conf import settings

        self.assertTrue(settings.AXES_ENABLE_ACCESS_FAILURE_LOG)

    def test_superuser_sees_all(self):
        """V31: superuser → all rows, including unattributable ones."""
        body = self.get(self.admin).json()
        # root's own login row is legitimately in the history.
        self.assertEqual({r["username"] for r in body["logs"]},
                         {"root", "ua", "ub", "uno"})
        self.assertEqual({r["username"] for r in body["failures"]}, {"ua", "ghost"})

    def test_org_user_sees_own_org_only(self):
        """V31: org admin → that org's usernames, never other tenants."""
        body = self.get(self.u_a).json()
        # ua2 has no fixture row; ua's own login row is legitimate.
        self.assertEqual({r["username"] for r in body["logs"]}, {"ua"})
        self.assertEqual({r["username"] for r in body["failures"]}, {"ua"})

    def test_org_b_admin_isolated(self):
        """V31: a second tenant sees only its own rows."""
        body = self.get(self.u_b).json()
        self.assertEqual({r["username"] for r in body["logs"]}, {"ub"})
        self.assertEqual(body["failures"], [])

    def test_no_org_user_sees_self_only(self):
        """V31: is_no_org → own username only."""
        body = self.get(self.u_no).json()
        self.assertEqual({r["username"] for r in body["logs"]}, {"uno"})
        self.assertEqual(body["failures"], [])

    def test_newest_first(self):
        """V29: explicit ordering — axes fields carry no Meta.ordering."""
        logs = self.get(self.admin).json()["logs"]
        times = [r["attempt_time"] for r in logs]
        self.assertEqual(times, sorted(times, reverse=True))
        self.assertGreater(len(times), 1)

    def test_payload_excludes_credentials(self):
        """V30: no path_info/session_hash/http_accept leaves the server."""
        body = self.get(self.admin).json()
        for row in body["logs"] + body["failures"]:
            self.assertNotIn("path_info", row)
            self.assertNotIn("session_hash", row)
            self.assertNotIn("http_accept", row)
        self.assertNotIn("secret-token", json.dumps(body))

    def test_readonly_does_not_mutate_axes(self):
        """V27: a read never resets or deletes axes state."""
        from axes.models import AccessFailureLog

        before = AccessFailureLog.objects.count()
        self.get(self.admin)
        self.assertEqual(AccessFailureLog.objects.count(), before)

class MemberWriteApiTests(TestCase):
    """SPEC §C/V41-V45: adopt/edit/delete mirror the admin, never drift."""

    @classmethod
    def setUpTestData(cls):
        from django.contrib.auth.models import Permission

        cls.features = Features.objects.create(name="W", number_of_member=10)
        with mock.patch.object(Controllers, "save", autospec=True):
            cls.org = Organizations(name="WriteOrg", features=cls.features)
            cls.org.save()
        with mock.patch(
            "controllers.backend.Zerotier.status", return_value=FAKE_STATUS
        ):
            cls.controller = Controllers(
                name="ctl", uri="http://controller:9993", token="tok"
            )
            cls.controller.save()

        cls.writer = User.objects.create_user(
            username="writer", email="w@t.co", password="x", organization=cls.org
        )
        cls.writer.user_permissions.add(
            *Permission.objects.filter(
                codename__in=["add_members", "change_members", "delete_members"]
            )
        )
        cls.admin = User.objects.create_superuser(
            username="root", email="r@t.co", password="x", organization=cls.org
        )

    def setUp(self):
        self.license = mock.patch(
            "members.permissions.is_license_valid", return_value=True
        )
        self.license.start()
        self.addCleanup(self.license.stop)

        with mock.patch.object(
            Controllers, "save", autospec=True
        ), mock.patch("networks.models.Zerotier") as zt_cls:
            zt = zt_cls.return_value
            zt.list_networks.return_value = []
            zt.add_network.return_value = dict(FAKE_NETWORK, nwid="nwid_w")
            zt.get_network_info.return_value = FAKE_NETWORK
            zt.set_network.return_value = FAKE_NETWORK
            self.net = Networks(
                name="WriteNet",
                controller=self.controller,
                organization=self.org,
                user=self.writer,
                network_id="nwid_w",
            )
            self.net.save()
        Networks.objects.filter(pk=self.net.pk).update(
            ip_address_networks="10.0.0.0/24"
        )
        self.net.refresh_from_db()

    def _post(self, user, body):
        self.client.force_login(user)
        return self.client.post(
            reverse("app_members"), json.dumps(body), content_type="application/json"
        )

    def _adopt(self, user, member_id="nodewrite1", **extra):
        info = {
            "id": member_id,
            "authorized": False,
            "activeBridge": False,
            "noAutoAssignIps": False,
            "ipAssignments": ["10.0.0.7"],
        }
        with mock.patch(
            "controllers.backend.Zerotier.get_member_info_ex",
            return_value=(200, info),
        ), mock.patch("members.models.Zerotier") as zt_cls, mock.patch.object(
            Members, "save", autospec=True
        ) as save:
            save.side_effect = lambda obj, *a, **k: None
            r = self._post(
                user,
                {"network_id": "nwid_w", "member_id": member_id, **extra},
            )
        return r, save

    def test_adopt_seeds_from_controller_not_defaults(self):
        """V41: a pending controller member is not authorized by adopting it."""
        r, save = self._adopt(self.writer, name="N1")
        self.assertEqual(r.status_code, 201)
        row = save.call_args.args[0]
        self.assertFalse(row.is_authorized)
        self.assertEqual(row.ipaddress, "10.0.0.7")
        self.assertEqual(row.name, "N1")

    def test_adopt_controller_unreachable_is_502(self):
        with mock.patch(
            "controllers.backend.Zerotier.get_member_info_ex",
            return_value=(None, None),
        ):
            r = self._post(
                self.writer, {"network_id": "nwid_w", "member_id": "nodewrite1"}
            )
        self.assertEqual(r.status_code, 502)

    def test_adopt_controller_absent_is_400(self):
        with mock.patch(
            "controllers.backend.Zerotier.get_member_info_ex",
            return_value=(404, None),
        ):
            r = self._post(
                self.writer, {"network_id": "nwid_w", "member_id": "nodewrite1"}
            )
        self.assertEqual(r.status_code, 400)

    def test_superuser_denied_before_controller(self):
        """§C: the rule check precedes any controller call."""
        with mock.patch(
            "controllers.backend.Zerotier.get_member_info_ex"
        ) as info:
            r = self._post(
                self.admin, {"network_id": "nwid_w", "member_id": "nodewrite1"}
            )
        self.assertEqual(r.status_code, 403)
        self.assertEqual(r.json()["rule"], "superuser_no_member_write")
        info.assert_not_called()

    def test_duplicate_adopt_is_400(self):
        with mock.patch("members.models.Zerotier") as zt_cls:
            zt_cls.return_value.set_member.return_value = FAKE_MEMBER
            zt_cls.return_value.get_member_peers.return_value = FAKE_PEERS
            Members(name="Dup", member_id="nodewrite1", network=self.net).save()
        r = self._post(
            self.writer, {"network_id": "nwid_w", "member_id": "nodewrite1"}
        )
        self.assertEqual(r.status_code, 400)
        self.assertIn("member_id", r.json()["error"])

    def test_db_unique_constraint(self):
        """V45: a concurrent adopt cannot slip a second row in."""
        from django.db import IntegrityError, transaction

        with mock.patch("members.models.Zerotier") as zt_cls:
            zt_cls.return_value.set_member.return_value = FAKE_MEMBER
            zt_cls.return_value.get_member_peers.return_value = FAKE_PEERS
            Members(name="One", member_id="nodewrite1", network=self.net).save()
        with self.assertRaises(IntegrityError), transaction.atomic():
            Members.objects.bulk_create(
                [Members(name="Two", member_id="nodewrite1", network=self.net)]
            )

    def test_foreign_member_is_404_not_403(self):
        """V3: scoping wins over permission, so tenants cannot probe IDs."""
        with mock.patch.object(Controllers, "save", autospec=True):
            other_org = Organizations(name="Other", features=self.features)
            other_org.save()
        with mock.patch("members.models.Zerotier") as zt_cls:
            zt_cls.return_value.set_member.return_value = FAKE_MEMBER
            zt_cls.return_value.get_member_peers.return_value = FAKE_PEERS
            foreign = Members(
                name="Foreign",
                member_id="foreign001",
                network=self.net,
                organization=other_org,
            )
            foreign.save()
        Members.objects.filter(pk=foreign.pk).update(organization=other_org)
        self.client.force_login(self.writer)
        r = self.client.get(reverse("app_member_detail", args=[foreign.member_id]))
        self.assertEqual(r.status_code, 404)

    def _member(self):
        with mock.patch("members.models.Zerotier") as zt_cls:
            zt = zt_cls.return_value
            zt.set_member.return_value = FAKE_MEMBER
            zt.get_member_peers.return_value = FAKE_PEERS
            m = Members(
                name="Editable",
                member_id="editme0001",
                network=self.net,
                ipaddress="10.0.0.9",
            )
            m.save()
        return m

    def test_patch_immutable_member_id_is_400(self):
        m = self._member()
        self.client.force_login(self.writer)
        r = self.client.patch(
            reverse("app_member_detail", args=[m.member_id]),
            json.dumps({"member_id": "other00001"}),
            content_type="application/json",
        )
        self.assertEqual(r.status_code, 400)
        m.refresh_from_db()
        self.assertEqual(m.member_id, "editme0001")

    def test_patch_saves_editable_field(self):
        m = self._member()
        self.client.force_login(self.writer)
        with mock.patch("members.models.Zerotier") as zt_cls:
            zt_cls.return_value.set_member.return_value = FAKE_MEMBER
            zt_cls.return_value.get_member_peers.return_value = FAKE_PEERS
            r = self.client.patch(
                reverse("app_member_detail", args=[m.member_id]),
                json.dumps({"name": "Renamed"}),
                content_type="application/json",
            )
        self.assertEqual(r.status_code, 200)
        m.refresh_from_db()
        self.assertEqual(m.name, "Renamed")

    def test_delete_controller_refusal_is_409_then_force_drops(self):
        """V42: force is only meaningful after the refusal, and logs it."""
        m = self._member()
        self.client.force_login(self.writer)
        with mock.patch(
            "controllers.backend.Zerotier.delete_member",
            return_value={"status": 0},
        ):
            r = self.client.delete(reverse("app_member_detail", args=[m.member_id]))
        self.assertEqual(r.status_code, 409)
        self.assertTrue(r.json()["force_available"])
        self.assertTrue(Members.objects.filter(pk=m.pk).exists())

        with self.assertLogs("app.views", level="WARNING"):
            r = self.client.delete(
                reverse("app_member_detail", args=[m.member_id]) + "?force=true"
            )
        self.assertEqual(r.status_code, 200)
        self.assertFalse(Members.objects.filter(pk=m.pk).exists())

    def test_picker_rejects_failure_dict(self):
        """V44: {'status': 0} must not become a member named 'status'."""
        self.client.force_login(self.writer)
        with mock.patch(
            "controllers.backend.Zerotier.list_members_ex",
            return_value=(None, {"status": 0}),
        ):
            r = self.client.get(
                reverse("app_network_controller_members", args=["nwid_w"])
            )
        self.assertEqual(r.status_code, 502)

    def test_picker_lists_only_unadopted(self):
        with mock.patch("members.models.Zerotier") as zt_cls:
            zt_cls.return_value.set_member.return_value = FAKE_MEMBER
            zt_cls.return_value.get_member_peers.return_value = FAKE_PEERS
            Members(name="Known", member_id="known00001", network=self.net).save()
        info = {
            "authorized": True,
            "activeBridge": False,
            "noAutoAssignIps": False,
            "ipAssignments": ["10.0.0.8"],
        }
        self.client.force_login(self.writer)
        with mock.patch(
            "controllers.backend.Zerotier.list_members_ex",
            return_value=(200, {"known00001": 1, "fresh00001": 1}),
        ), mock.patch(
            "controllers.backend.Zerotier.get_member_info_ex",
            return_value=(200, info),
        ):
            r = self.client.get(
                reverse("app_network_controller_members", args=["nwid_w"])
            )
        self.assertEqual(r.status_code, 200)
        self.assertEqual(
            r.json(),
            [{"member_id": "fresh00001", "authorized": True, "ipaddress": "10.0.0.8"}],
        )

    def test_me_permissions_block(self):
        """§C: capability comes from the server, superuser add/edit denied."""
        self.client.force_login(self.admin)
        perms = self.client.get(reverse("app_me")).json()["permissions"]
        self.assertFalse(perms["members_add"])
        self.assertFalse(perms["members_change"])
        self.assertTrue(perms["members_delete"])
        self.assertEqual(perms["reasons"]["add"], "superuser_no_member_write")

        self.client.force_login(self.writer)
        perms = self.client.get(reverse("app_me")).json()["permissions"]
        self.assertTrue(perms["members_add"])
        self.assertTrue(perms["members_change"])
        self.assertTrue(perms["members_delete"])
