from django.db.transaction import Atomic
import redis

# from datetime import datetime
# from os import walk
from crum import get_current_user
from django.db import models
from django.utils import timezone
from config.utils import get_uptime_string, get_cpu_usage
from django.conf import settings
from accounts.models import User, Organizations
from networks.models import Networks, NetworkRoutes
from monitor.utils import check_members_vs_rules

# from monitor.models import MonitorRules
from django.utils.translation import gettext as _
from django.utils.html import format_html
from controllers.backend import Zerotier
from django.core.validators import RegexValidator
from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned
from config.utils import to_dictionary, readable_timedelta, calculate_bandwidth_unit
from ipaddress import ip_address, ip_network
from datetime import datetime
from django.core.exceptions import ValidationError
from mqtt.models import Mqtt
from mqtt.redis import (
    get_msg,
    get_msg_ts,
    get_msg_by_index,
    get_parameter_by_index,
)


"""
MemberPeers Model
"""


class MemberPeers(models.Model):
    peers = models.TextField(_("Peers"))
    member_id = models.CharField(_("Member ID"), max_length=50)
    network = models.ForeignKey(
        Networks,
        on_delete=models.CASCADE,
        verbose_name=_("Network"),
    )

    created_at = models.DateTimeField(auto_now=False, auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True, auto_now_add=False)

    class Meta:
        db_table = "member_peers"
        verbose_name = "member peer"
        verbose_name_plural = "member peers"

    def __str__(self):
        return "%s" % self.peers

    def save(self):
        zt = Zerotier(self.network.controller.uri, self.network.controller.token)
        self.peers = zt.get_member_peers(self.member_id)
        return super(MemberPeers, self).save()


class Members(models.Model):
    def limit_choices_to_current_user():
        user = get_current_user()
        if not user.is_superuser:
            if user.organization.is_no_org:
                return {"user": user}
            else:
                return {"organization": user.organization}
        else:
            return {}

    name = models.CharField(_("Member Name"), max_length=50)
    member_code = models.CharField(
        _("Member Code"), max_length=20, blank=True, null=True
    )
    description = models.TextField(_("Description"), blank=True)
    member_id = models.CharField(_("Member ID"), max_length=50)
    network = models.ForeignKey(
        Networks,
        on_delete=models.CASCADE,
        limit_choices_to=limit_choices_to_current_user,
        verbose_name=_("Network"),
    )
    user = models.ForeignKey(
        User, on_delete=models.SET_NULL, verbose_name=_("Owner"), null=True
    )
    organization = models.ForeignKey(
        Organizations,
        on_delete=models.SET_NULL,
        verbose_name=_("Organization"),
        null=True,
    )

    is_bridge = models.BooleanField(_("Bridge Mode"), default=False)
    is_no_auto_ip = models.BooleanField(_("No Auto Assign IP"), default=False)
    is_authorized = models.BooleanField(_("Authorized"), default=True)
    tags = models.CharField(
        _("Tags"),
        max_length=50,
        blank=True,
        null=True,
        help_text=_("Example: ssh_client"),
    )
    ipaddress = models.CharField(_("IP Address"), max_length=100, blank=True, null=True)
    # serialnumber = models.CharField(_('SN'), max_length=100, blank=True, null=True)
    address = models.CharField(max_length=250, blank=True, null=True)
    location = models.CharField(max_length=250, blank=True, null=True)
    online_at = models.DateField(_("Start Online"), blank=True, null=True)
    offline_at = models.DateTimeField(_("Stop Online"), blank=True, null=True)

    # DPI Netify
    is_dpi = models.BooleanField(_("DPI"), default=False)

    # WAF
    is_waf = models.BooleanField(_("WebFilter Active"), default=False)

    # Mobile
    mobile_regex = RegexValidator(
        regex=r"^62\d{9,15}$",
        message=_(
            "Mobile number must be entered in the format: '628XXXXXXXXXXX'. Up to 15 digits allowed."
        ),
    )
    mobile_number_first = models.CharField(
        _("Mobile Number/Service Line"),
        # validators=[mobile_regex],
        max_length=20,
        blank=True,
        null=True,
    )

    configuration = models.TextField(_("Configuration"), blank=True)

    peers = models.ForeignKey(
        MemberPeers, on_delete=models.SET_NULL, verbose_name=_("Peers"), null=True
    )

    mqtt = models.ForeignKey(
        Mqtt, on_delete=models.SET_NULL, verbose_name=_("Mqtt"), null=True
    )

    created_at = models.DateTimeField(auto_now=False, auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True, auto_now_add=False)

    class Meta:
        db_table = "members"
        verbose_name = "member"
        verbose_name_plural = "members"

    def __str__(self):
        return "%s" % self.name

    def delete(self, using=None, keep_parents=False):
        zt = Zerotier(self.network.controller.uri, self.network.controller.token)
        zt.delete_member(self.network.network_id, self.member_id)
        return super(Members, self).delete()

    def save(self):
        self.user = self.network.user
        self.organization = self.network.organization
        if self.member_code:
            self.member_code = self.member_code.upper()

        # Zerotier
        zt = Zerotier(self.network.controller.uri, self.network.controller.token)

        # Authorized and Bridge Setting
        data = {
            "authorized": self.is_authorized,
            "activeBridge": self.is_bridge,
            "noAutoAssignIps": self.is_no_auto_ip,
        }

        # Assign IP Address
        if self.ipaddress is not None:
            self.ipaddress = self.ipaddress.replace(" ", "")
            ip_address_lists = self.ipaddress.split(",")
            data["ipAssignments"] = ip_address_lists

        # Apply Configuration to controller
        print("Member", self.member_id, data)
        member_info = zt.set_member(self.network.network_id, self.member_id, data)
        self.configuration = member_info

        # Get MemberPeers
        try:
            member_peers = MemberPeers.objects.get(member_id=self.member_id)
        except ObjectDoesNotExist:
            member_peers = MemberPeers(member_id=self.member_id)
        except MultipleObjectsReturned:
            # member_peers = MemberPeers.objects.filter(member_id=self.member_id).first()
            member_peers = MemberPeers.objects.filter(member_id=self.member_id).delete()
            member_peers = MemberPeers(member_id=self.member_id)
        member_peers.peers = zt.get_member_peers(self.member_id)
        member_peers.network = self.network
        member_peers.save()
        self.peers = member_peers

        if self.mqtt is None:
            try:
                mqtt = Mqtt.objects.get(member_id=self.member_id)
                self.mqtt = mqtt
            except ObjectDoesNotExist:
                pass

        return super(Members, self).save()

    def clean(self):
        try:
            self.network.network_id
        except ObjectDoesNotExist:
            raise ValidationError({"network": _("Please choose Network")})

        # if self.network is None:
        #    raise ValidationError({'Network': _('Please choose Network')})

        # Check mobile_number_first is not Unique
        if self.mobile_number_first is not None:
            try:
                Members.objects.exclude(id=self.id).get(
                    mobile_number_first=self.mobile_number_first
                )
                raise ValidationError(
                    {"mobile_number_first": _("Mobile Number is already used!")}
                )
            except ObjectDoesNotExist:
                pass

        # Check if member_id is already in this network

        if self.member_id:
            if self.id is None:
                try:
                    Members.objects.get(member_id=self.member_id, network=self.network)
                    raise ValidationError(
                        {"member_id": _("Member ID already exist in this network!")}
                    )
                except ObjectDoesNotExist:
                    pass
            if len(self.member_id) != 10:
                raise ValidationError(
                    {"member_id": _("Member ID must be 10 characters!")}
                )

        # CHECK: For multiple IP in self.ipaddress
        # Check for list IP_address
        if self.ipaddress is not None:
            self.ipaddress = self.ipaddress.replace(" ", "")
            ip_address_lists = self.ipaddress.split(",")

            for ip_address_list in ip_address_lists:
                try:
                    ip_address(ip_address_list)
                except ValueError:
                    raise ValidationError({"ipaddress": _("Wrong Format")})

            # New Block Validation compare to ip_network
            if self.network.ip_address_networks is not None:
                ip_network_lists = self.network.ip_address_networks.split(",")

                # is_ipaddress_in_network = False
                ip_status = {}
                for ip_address_list in ip_address_lists:
                    ip_status[ip_address_list] = False
                    print(ip_address_list)
                    for ip_network_list in ip_network_lists:
                        print(ip_network_list)
                        if ip_address(ip_address_list) in ip_network(ip_network_list):
                            is_ipaddress_in_network = True
                            ip_status[ip_address_list] = True
                            break
                        # else:
                        # is_ipaddress_in_network = False
                # print(ip_status)
                # if not is_ipaddress_in_network:
                for ip_address_list in ip_address_lists:
                    if not ip_status[ip_address_list]:
                        raise ValidationError(
                            {
                                "ipaddress": _(
                                    "IP address should be in segment "
                                    + self.network.ip_address_networks
                                )
                            }
                        )

                # Second Raise
                for ip_address_list in ip_address_lists:

                    """Optimize this for different network"""
                    """adding: network=self.network"""
                    members = Members.objects.filter(
                        ipaddress__contains=ip_address_list, network=self.network
                    ).exclude(member_id=self.member_id)

                    if members:
                        is_duplicate = False
                        for member in members:
                            if "," in member.ipaddress:
                                m_ipaddress = member.ipaddress.split(",")
                                for m_ip in m_ipaddress:
                                    if m_ip == ip_address_list:
                                        is_duplicate = True
                            elif member.ipaddress == ip_address_list:
                                is_duplicate = True
                        if is_duplicate:
                            raise ValidationError(
                                {
                                    "ipaddress": _(
                                        "IP address "
                                        + ip_address_list
                                        + " is already used!"
                                    )
                                }
                            )
            else:
                raise ValidationError(
                    _("First, please setup IP Network in " + self.network.name)
                )

    def list_ipaddress(self):
        text = ""

        if self.ipaddress is not None:
            ipaddress_list = self.ipaddress.split(",")
            text = format_html("<br />".join([str(p) for p in ipaddress_list]))

        is_authorized = "icon-yes.svg" if self.is_authorized else "icon-no.svg"
        # return text

        # Get Hostname from MQTT
        if self.get_hostname():
            text = format_html("{}<br />{}", self.get_hostname(), text)

        if self.mobile_number_first is not None:
            if text == "":
                text = format_html("{}", self.mobile_number_first)
            else:
                text += format_html("<br />{}", self.mobile_number_first)

        return format_html(
            "<small>"
            + "<strong>{}</strong>"
            + " <img src='/static/admin/img/{}'>"
            + "<br />{}"
            + "<br />{}</small>",
            self.member_id,
            is_authorized,
            text,
            self.network.name,
        )

    list_ipaddress.short_description = _("ID, IP and Network")

    def list_peers(self):
        peers = to_dictionary("{}")
        if self.peers:
            peers = to_dictionary(self.peers.peers)
        if "paths" in peers and len(peers["paths"]) != 0:
            paths = peers["paths"]
            ip_peers = []
            ip_peers_html = []
            for path in paths:
                ip_path = path["address"].split("/")
                if ip_path[0] not in ip_peers:
                    ip_info = "<a href='https://ipinfo.io/{}' target='_blank' rel='noopener noreferrer'>{}</a>".format(
                        ip_path[0], ip_path[0]
                    )
                    ip_peers.append(ip_path[0])
                    ip_peers_html.append(ip_info)

            result = "<br />".join([str(p) for p in ip_peers_html])
            return format_html("<small>" + result + "</small>")
        else:
            return ""

    list_peers.short_description = _("Peers          ")

    def member_status(self):
        peers = to_dictionary("{}")
        if self.peers:
            peers = to_dictionary(self.peers.peers)

        if "paths" in peers and len(peers["paths"]) != 0:
            version = peers["version"]
            latency = peers["latency"]

            if latency < 0:
                direct_or_relay = "RELAY"
                text = format_html("<small>{} ({})</small>", direct_or_relay, version)
            else:
                direct_or_relay = "DIRECT"
                text = format_html(
                    "<small>{} ({}/{}ms)</small>",
                    direct_or_relay,
                    version,
                    str(latency),
                )

            # text = format_html("<small style='color: green;'>ONLINE ({})<br />{}({}ms)<br />{}</small>",
            #                   version, peers['role'], str(latency), direct_or_relay)
            # text = format_html("<small style='color: green;'>{} ({}/{}ms)</small>",
            #                   direct_or_relay, version, str(latency))
        else:
            controller_configuration = to_dictionary(
                self.network.controller.configuration
            )
            if self.peers:
                peers = to_dictionary(self.peers.peers)

            if self.member_id == controller_configuration["address"]:
                version = controller_configuration["version"]
                text = format_html(
                    "<small style='color: blue;'>CONTROLLER ({})</small>", version
                )
            elif self.peers:
                if (
                    "role" in self.peers.peers
                    and "latency" in self.peers.peers
                    and "version" in self.peers.peers
                ):  # and int(self.peers.peers['latency']) == -1:
                    text = format_html("<small>RELAY ({})</small>", peers["version"])
                else:
                    text = format_html("<small style='color: red;'>OFFLINE</small>")
            else:
                text = format_html("<small style='color: red;'>OFFLINE</small>")

        # return text
        ipaddress_ts = self.ipaddress_ts()
        if ipaddress_ts:
            text = format_html(
                self.list_ipaddress()
                + "<br />"
                + text
                + "<br /><small>IP TS: "
                + ipaddress_ts
                + "</small>"
            )
        else:
            text = format_html(self.list_ipaddress() + "<br />" + text)

        if self.is_waf:
            # text += format_html(text + "<br /><small>WAF: On</small>")
            text = format_html(text + "<br /><small>WAF: On</small>")
        else:
            text = format_html(text + "<br /><small>WAF: Off</small>")

        if self.is_dpi:
            netify_uuid = self.netify_uuid()
            if netify_uuid:
                text = format_html(text + f"<br /><small>DPI: {netify_uuid}</small>")
            else:
                text = format_html(text + "<br /><small>DPI: On</small>")
        else:
            text = format_html(text + "<br /><small>DPI: Off</small>")

        return text

    member_status.short_description = _("Member Status")
    member_status.admin_order_field = "network"

    def is_online(self):
        online_status = False
        peers = to_dictionary("{}")
        # if self.peers:
        try:
            self.peers
            try:
                peers = to_dictionary(self.peers.peers)
                if "paths" in peers and len(peers["paths"]) != 0 and self.ipaddress:
                    online_status = True
                if (
                    "role" in self.peers.peers
                    and "latency" in self.peers.peers
                    and "version" in self.peers.peers
                ):  # and int(self.peers.peers['latency']) == -1:
                    online_status = True
            except AttributeError:
                pass
        # except KeyError or ObjectDoesNotExist:
        except ObjectDoesNotExist:
            pass

        return online_status

    is_online.short_description = _("BackOne Online")

    def online_status(self):
        text = "OFFLINE"
        color = "red"
        if self.is_online():
            text = "ONLINE"
            color = "green"

        return format_html("<span style='color: " + color + ";'>" + text + "</span>")

    online_status.short_description = _("Online Status")

    def get_routes(self):
        routes = []
        net_routes = NetworkRoutes.objects.filter(
            network=self.network, gateway=self.ipaddress
        )
        text = format_html(
            "<small>" + "<br />".join([str(p) for p in net_routes]) + "</small>"
        )
        return text

    get_routes.short_description = _("Routes")

    def get_routes_plain(self):
        routes = []
        net_routes = NetworkRoutes.objects.filter(
            network=self.network, gateway=self.ipaddress
        )
        text = ", ".join([str(p) for p in net_routes])
        return text

    get_routes_plain.short_description = _("Local Routes")

    def is_mqtt_online(self):
        online_status = False

        # msg = get_msg(self.member_id)
        msg_ts = get_msg_ts(self.member_id)
        if msg_ts:
            delta_time = int(timezone.now().timestamp()) - (
                msg_ts + settings.ONLINE_STATUS_DELAY
            )
            if delta_time < 0:
                online_status = True

        return online_status

    is_mqtt_online.short_description = _("Internet Online")

    def get_hostname(self):
        hostname = get_msg_by_index(self.member_id, 19)  # Index 19 -> Hostname

        return hostname

    def get_alarms(self):
        result = []
        if self.organization:
            if self.organization.features.is_nms:
                # rules = check_members_vs_rules(self, self.is_online())
                rules = check_members_vs_rules(self, True)
                for rule in rules:
                    result.append(rule.item.item_id)
        return result

    def num_core(self):
        parameter = get_msg_by_index(self.member_id, 9)  # Index 9 -> Number of Core
        result = int(parameter) if parameter else 1

        return result

    def memory_usage(self):
        parameter = get_msg_by_index(self.member_id, 10)  # Index 10 -> Memory Usage
        result = float(parameter) if parameter else 0.0

        return result

    def cpu_usage(self):
        if self.uptime_string():
            load_1, load_5, load_15 = get_cpu_usage(
                self.uptime_string(), self.num_core()
            )
        else:
            load_1 = load_5 = load_15 = 0.0

        return round(load_5, 1)

    def packet_loss(self):
        parameter = get_msg_by_index(
            self.member_id, 11
        )  # Index 11 -> Packet Loss String
        result = -1.0
        if parameter:
            packet_loss_split = str(parameter).split(",")
            packet_loss_digit_string = packet_loss_split[2].split("%")

            try:
                packet_loss = float(packet_loss_digit_string[0])
            except ValueError:
                packet_loss = -1
                # packet_loss = 0

            result = packet_loss

        return result

    def round_trip(self):
        parameter = get_msg_by_index(
            self.member_id, 12
        )  # Index 12 -> Round Trip String
        result = -1.0

        if parameter:
            round_trip_string = str(parameter).split("=")
            round_trip_digit = round_trip_string[1].split("/")

            try:
                round_trip = float(round_trip_digit[1])
            except ValueError:
                round_trip = -1

            result = round_trip

        return result

    def ipaddress_ts(self):
        result = get_msg_by_index(
            self.member_id, 16
        )  # Index 16 -> IP Address TailScale
        return result

    def uptime(self):
        result = get_msg_by_index(self.member_id, 7)  # Index 7 -> Uptime
        if result:
            uptime_load = get_uptime_string(result)
            uptime_split = uptime_load.split("load average")
            result = uptime_split[0][:-3:]

        return result.strip()

    def uptime_string(self):
        result = get_msg_by_index(self.member_id, 7)  # Index 7 -> Uptime
        return result

    def serialnumber(self):
        result = get_msg_by_index(self.member_id, 8)  # Index 8 -> Serial Number
        return result

    def model(self):
        result = get_msg_by_index(self.member_id, 1)  # Index 1 -> model
        return result

    def board_name(self):
        result = get_msg_by_index(self.member_id, 2)  # Index 2 -> board_name
        return result

    def release_version(self):
        result = get_msg_by_index(self.member_id, 3)  # Index 3 -> release_version
        return result

    def release_target(self):
        result = get_msg_by_index(self.member_id, 4)  # Index 4 -> release_target
        return result

    def netify_uuid(self):
        result = get_msg_by_index(self.member_id, 20)  # Index 20 -> netify_uuid
        return result

    def model_release(self):
        text = None

        msg = get_msg(self.member_id)
        if msg:
            mqtt = self.mqtt
            alarms = self.get_alarms()
            """
            updated_at = timezone.localtime(mqtt.updated_at).strftime(
                "%d-%m-%Y, %H:%M:%S"
            )
            """
            ts_unix = get_msg_ts(self.member_id)
            updated_at = timezone.make_aware(datetime.fromtimestamp(ts_unix))
            # is_authorized = "icon-yes.svg" if self.is_authorized else "icon-no.svg"

            """ First Line: Model and CPU Core"""
            first_line = ""
            model_string = self.model()
            num_core = self.num_core()

            if model_string:
                first_line = "<small>{} ({})</small>".format(model_string, num_core)

            """ Second Line: SerialNumber and Release Version"""
            second_line = ""
            second_line_var = ""
            serialnumber_string = self.serialnumber()
            release_version_string = self.release_version()

            if serialnumber_string or release_version_string:
                second_line_var = (
                    serialnumber_string + " - " + release_version_string
                    if serialnumber_string
                    else release_version_string
                )

                if second_line_var:
                    second_line = "<br />"
                    second_line += "<small>{}</small>".format(second_line_var)
                    # second_line += "{} <img src='/static/admin/img/{}'>".format(
                    #        second_line_var, is_authorized) if self.is_authorized else second_line_var

            """ Third Line: SwitchPortUp and PortStatus"""
            third_line = ""
            switchport_up_string = self.switchport_up()
            port_status_string = self.port_status()

            if switchport_up_string:
                third_line += "<br /><small>"
                third_line += "<span>SwPortUP: {}</span>".format(switchport_up_string)
                third_line += "</small>"

            if port_status_string:
                third_line += "<br /><small>"
                third_line += "<span>PortStat: {}</span>".format(port_status_string)
                third_line += "</small>"

            """ Fourth Line: Uptime, CPU and Memory """
            fourth_line = ""
            uptime = self.uptime()
            if uptime:
                fourth_line = "<br /><small>"

                """ UPTIME """
                fourth_line += "<span>UP: {}</span>".format(uptime)

                """ CPU """
                item_id = "cpu_usage"
                value = self.cpu_usage()
                color = "red" if item_id in alarms else ""
                fourth_line += " - <span style='color: {};'>CPU: {}%</span>".format(
                    color, value
                )

                """ MEMORY """
                item_id = "memory_usage"
                value = self.memory_usage()
                color = "red" if item_id in alarms else ""
                fourth_line += " - <span style='color: {};'>MEM: {}%</span>".format(
                    color, value
                )

                """ PACKET LOSS """
                item_id = "packet_loss"
                value_pl = self.packet_loss()
                # value_rt = self.round_trip()
                color = "red" if item_id in alarms else ""
                # if value_rt:
                if value_pl >= 0:
                    fourth_line += (
                        "<br /><span style='color: {};'>PL: {}% - </span>".format(
                            color, value_pl
                        )
                    )

                """ ROUND_TRIP """
                item_id = "round_trip"
                # value = self.round_trip()
                value_rt = self.round_trip()
                color = "red" if item_id in alarms else ""
                if value_rt > 0:
                    fourth_line += "<span style='color: {};'>RT: {}ms<span>".format(
                        color, value_rt
                    )

                fourth_line += "</small>"

            """ Fifth line QUOTA FIRST """
            fifth_line = ""

            quota_current, quota_total, quota_day, quota_type = (
                self.mqtt.get_quota_first()
            )

            # if not quota_current==0 and not quota_total==0 and not quota_day==0:
            quota_current = quota_current / 1024
            if not quota_total == 0:
                item_id = "quota_first_gb"
                color = "red" if item_id in alarms else ""
                quota_text = ""
                # color = '' if quota_current > settings.QUOTA_GB_WARNING else 'red'
                quota_text += "<span style='color: {};'>{}GB</span>".format(
                    color, quota_current
                )

                quota_text += "<span>/{}GB/</span>".format(quota_total)

                item_id = "quota_first_day"
                color = "red" if item_id in alarms else ""
                # color = '' if quota_day > settings.QUOTA_DAY_WARNING else 'red'
                quota_text += "<span style='color: {};'>{}Hari</span>".format(
                    color, quota_day
                )

                if quota_type:
                    quota_text += "<span>/{}</span>".format(quota_type.upper())

                fifth_line = "<br /><small>QUO: {}</small>".format(quota_text)

            quota_current_prev, quota_total_prev, quota_day_prev, quota_type_prev = (
                self.mqtt.get_quota_first_prev()
            )
            quota_current_prev = quota_current_prev / 1024

            if not quota_total_prev == 0:
                item_id = "quota_first_high_gb"
                color = "red" if item_id in alarms else ""
                quota_text_prev = ""
                # color = '' if quota_current > settings.QUOTA_GB_WARNING else 'red'
                quota_text_prev += "<span style='color: {};'>{}GB</span>".format(
                    color, quota_current_prev
                )

                quota_text_prev += "<span>/{}GB/</span>".format(quota_total_prev)

                quota_text_prev += "<span>{}Hari</span>".format(quota_day_prev)

                if quota_type_prev:
                    quota_text += "<span>/{}</span>".format(quota_type_prev.upper())

                fifth_line += "<br /><small>QUO_PREV: {}</small>".format(
                    quota_text_prev
                )

            sixth_line = ""
            vnstat_text = self.quota_vnstat()
            if vnstat_text != "":
                sixth_line = "<br /><small>QUSE: {}</small>".format(vnstat_text)

            """ Combine All Lines """
            if self.is_mqtt_online():
                text = format_html(
                    first_line
                    + second_line
                    + third_line
                    + fourth_line
                    + fifth_line
                    + sixth_line
                )

            else:
                text = format_html(
                    first_line
                    + second_line
                    + third_line
                    + fourth_line
                    + fifth_line
                    + sixth_line
                    + "<br /><small style='color: red;'>LU: {} ago</span></small>",
                    # readable_timedelta(mqtt.updated_at),
                    readable_timedelta(updated_at),
                )

            # if not mqtt.uptime:
            if not uptime:
                text = format_html(
                    first_line
                    + second_line
                    + third_line
                    + fourth_line
                    + fifth_line
                    + sixth_line
                )

        return text

    model_release.short_description = _("Parameters")
    model_release.admin_order_field = "mqtt__model"

    def member_name_with_address(self):
        text = self.name
        if self.address:
            address_html = format_html(self.address.replace(",", "<br />"))
            text = format_html("{}<br /><small>{}</small>", self.name, address_html)
        return text

    member_name_with_address.short_description = _("Member Name")
    member_name_with_address.admin_order_field = "name"

    def switchport_up(self):
        result = get_msg_by_index(self.member_id, 13)  # Index 13 -> Switch Port
        return result

    switchport_up.short_description = _("Switch Port UP")

    def port_status(self):
        result = get_msg_by_index(self.member_id, 14)  # Index 14 -> Port Status
        return result

    port_status.short_description = _("Port Status")

    def quota_vnstat(self):
        rx_usage = 0
        tx_usage = 0
        total_usage = 0
        split_text = []

        parameter = get_msg_by_index(self.member_id, 15)  # Index 15 -> Quota VNSTAT
        result = ""
        if parameter:
            split_text = str(parameter).split(",")

            """ RX Usage """
            try:
                rx_usage = int(split_text[2])
            except (IndexError, ValueError):
                pass

            """ TX Usage """
            try:
                tx_usage = int(split_text[3])
            except (IndexError, ValueError):
                pass

            """ Total Usage """
            try:
                total_usage = int(split_text[4])
            except (IndexError, ValueError):
                pass

            total_unit, total_value = calculate_bandwidth_unit(total_usage_value)
            if total_value:  # Only show if not 0
                result = str(round(total_value, 2)) + total_unit

        return result

    quota_vnstat.short_description = _("Quota Usage")

    def quota_first(self):
        quota_string = None
        # quota_current = 0
        # quota_total = 0
        # quota_day = 0
        # quota_type = None
        if self.mqtt:
            quota_string_split = str(self.mqtt.quota_first).split("/")
            quota_string = quota_string_split[0]
            # quota_current, quota_total, quota_day, quota_type = (
            # self.mqtt.get_quota_first()
            # )
        return quota_string

    def rssi(self):
        parameter = get_msg_by_index(self.member_id, 18)  # Index 18 -> RSSI

        if parameter:
            rssi_signal = int(parameter)
        else:
            rssi_signal = 99999

        text = "N/A"
        color = "black"
        if rssi_signal <= 65:
            text = "EXCELLENT"
            color = "blue"
        elif rssi_signal > 65 and rssi_signal <= 80:
            text = "GOOD"
            color = "green"
        elif rssi_signal != 99999:
            text = "NOT GOOD"
            color = "red"

        # return text
        return format_html("<span style='color: {};'>{}</span>", color, text)

    rssi.short_description = _("LTE Signal")
