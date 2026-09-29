import json
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.conf import settings
from django.views.decorators.cache import never_cache
from django.core.exceptions import ValidationError

from members.models import Members, MemberPeers
from members.views import prepare_data
from networks.models import Networks, NetworkRoutes
from controllers.models import Controllers
from controllers.backend import Zerotier
from connectors.redis_ipinfo import get_ip_loc
import subprocess
from networks.models import NetworkRules
from mqtt.models import Mqtt
from monitor.models import MonitorRules, MonitorItems, OperationalTime
from accounts.models import Features, Organizations, Devices
from webfilters.models import WebFilters, WebFiltersOrg, WebFiltersMembers
from zabbix.models import ZabbixConfigs
from licenses.models import Licenses
from headscale.models import HS_Users, HS_Nodes, HS_Preauthkeys
from problems.models import MemberProblems


def member_qs(request):
    """Org-scoped member queryset — mirrors Members.limit_choices_to_current_user."""
    if request.user.is_superuser:
        return Members.objects.all()
    if request.user.organization.is_no_org:
        return Members.objects.filter(user=request.user)
    return Members.objects.filter(organization=request.user.organization)


def network_qs(request):
    """Org-scoped network queryset — mirrors Networks.limit_choices_to_current_user."""
    if request.user.is_superuser:
        return Networks.objects.all()
    if request.user.organization.is_no_org:
        return Networks.objects.filter(user=request.user)
    return Networks.objects.filter(organization=request.user.organization)


def problem_qs(request):
    return MemberProblems.unsolved.all().filter(member__in=member_qs(request))

@login_required
@never_cache
def me(request):
    user = request.user
    org = user.organization
    data = {
        "user": {
            "id": user.id,
            "username": user.username,
            "name_or_email": user.email or user.username,
        },
        "organization": {
            "uuid": org.uuid if org else None,
            "name": org.name if org else None,
            "is_no_org": org.is_no_org if org else None,
        },
        "is_superuser": user.is_superuser,
        "features": {
            "is_2fa": getattr(settings, "IS_2FA_ENABLE", False),
            "is_mailauth_no_password": getattr(
                settings, "IS_MAILAUTH_NO_PASSWORD", False
            ),
        },
    }
    return JsonResponse(data)

def _parse_lat_lng(location):
    """Parse `name;POINT(lng lat)` (Wagtail GeoWidget) -> (lat, lng) floats. Fallback to GEO_WIDGET_DEFAULT_LOCATION."""
    if not location:
        default = settings.GEO_WIDGET_DEFAULT_LOCATION
        return default["lat"], default["lng"]
    try:
        point = location.split(";")
        result = point[1].split(" ")
        lng = float(result[0].replace("POINT(", ""))
        lat = float(result[1].replace(")", ""))
    except (IndexError, ValueError, AttributeError):
        default = settings.GEO_WIDGET_DEFAULT_LOCATION
        return default["lat"], default["lng"]
    return lat, lng

def _mqtt_summary(m):
    return {
        "cpu_usage": m.cpu_usage,
        "memory_usage": m.memory_usage,
        "packet_loss": m.get_packet_loss(),
        "round_trip": m.get_round_trip(),
        "uptime": m.uptime,
        "rssi_signal": m.rssi_signal,
        "updated_at": m.updated_at.isoformat() if m.updated_at else None,
    }

@login_required
@never_cache
def members(request):
    problems = list(problem_qs(request))
    members = list(member_qs(request).order_by("name"))
    data = prepare_data(members, problems)

    member_ids = [m.member_id for m in members]
    mqtt_by_member_id = {
        m.member_id: m for m in Mqtt.objects.filter(member_id__in=member_ids)
    }
    member_by_id = {m.id: m for m in members}

    for entry in data:
        member = member_by_id[entry["id"]]
        entry["network_id"] = member.network.network_id
        entry["organization"] = (
            str(member.organization.uuid) if member.organization else None
        )
        real_lat, real_lng = _parse_lat_lng(member.location)
        entry["lat"] = real_lat
        entry["lng"] = real_lng
        m = mqtt_by_member_id.get(member.member_id)
        if m:
            entry["mqtt"] = _mqtt_summary(m)
    return JsonResponse(data, safe=False)

@login_required
@never_cache
def member_telemetry(request, member_id):
    member = member_qs(request).filter(member_id=member_id).first()
    if member is None:
        return JsonResponse({"error": "not found"}, status=404)
    problems = MemberProblems.unsolved.filter(member=member)
    network = member.network
    data = {
        "member": {
            "member_id": member.member_id,
            "name": member.name,
            "member_code": member.member_code,
            "description": member.description,
            "address": member.address,
            "location": member.location,
            "ipaddress": member.ipaddress,
            "is_online": 1 if member.is_online() else 0,
            "is_authorized": 1 if member.is_authorized else 0,
            "is_bridge": member.is_bridge,
            "is_no_auto_ip": member.is_no_auto_ip,
            "is_dpi": member.is_dpi,
            "is_waf": member.is_waf,
            "tags": member.tags,
            "mobile_number_first": member.mobile_number_first,
            "online_at": member.online_at.isoformat() if member.online_at else None,
            "offline_at": (
                member.offline_at.isoformat() if member.offline_at else None
            ),
            "deauth_timer": member.deauth_timer,
            "deauth_timer_start": (
                member.deauth_timer_start.isoformat()
                if member.deauth_timer_start
                else None
            ),
            "created_at": member.created_at.isoformat() if member.created_at else None,
            "updated_at": member.updated_at.isoformat() if member.updated_at else None,
            "organization": member.organization.name if member.organization else None,
            "network": (
                {"network_id": network.network_id, "name": network.name}
                if network
                else None
            ),
            "is_problem": 1 if problems.exists() else 0,
            "lat": _parse_lat_lng(member.location)[0],
            "lng": _parse_lat_lng(member.location)[1],
        },
        "mqtt": None,
        "problems": [
            {
                "problem": p.problem.name if p.problem else None,
                "start_at": p.start_at.isoformat() if p.start_at else None,
                "duration": p.duration,
            }
            for p in problems
        ],
    }
    m = Mqtt.objects.filter(member_id=member.member_id).first()
    if m:
        quota_current, quota_total, quota_day, quota_type = m.get_quota_first()
        quota_prev, quota_prev_total, quota_prev_day, _ = m.get_quota_first_prev()
        load_1, load_5, load_15 = m.get_cpu_usage()
        rx_usage, tx_usage, total_usage = m.get_quota_vnstat()
        data["mqtt"] = {
            **_mqtt_summary(m),
            "num_core": m.num_core,
            "hostname": m.hostname,
            "model": m.model,
            "board_name": m.board_name,
            "release_version": m.release_version,
            "release_target": m.release_target,
            "serialnumber": m.serialnumber,
            "switchport_up": m.switchport_up,
            "port_status": m.port_status,
            "ipaddress_ts": m.ipaddress_ts,
            "is_rcall": m.is_rcall,
            "is_waf": m.is_waf,
            "netify_uuid": m.netify_uuid,
            "quota_first": m.quota_first,
            "quota_first_raw": m.quota_first,
            "quota_first_current": quota_current,
            "quota_first_total": quota_total,
            "quota_first_day": quota_day,
            "quota_type": quota_type,
            "quota_prev": quota_prev,
            "quota_prev_total": quota_prev_total,
            "quota_prev_day": quota_prev_day,
            "quota_prev_raw": m.quota_first_prev,
            "quota_vnstat": m.quota_vnstat,
            "rx_usage": rx_usage,
            "tx_usage": tx_usage,
            "total_usage": total_usage,
            "load_1": load_1,
            "load_5": load_5,
            "load_15": load_15,
            "uptime_string": m.get_uptime_string(),
            "ipaddress": m.ipaddress,
            "created_at": m.created_at.isoformat() if m.created_at else None,
            "is_online": 1 if m.is_online() else 0,
        }
    return JsonResponse(data)

@login_required
@never_cache
def networks(request):
    data = []
    for net in network_qs(request):
        data.append(
            {
                "network_id": net.network_id,
                "name": net.name,
                "description": net.description,
                "ip_allocation": net.ip_allocation(),
                "member_count": Members.objects.filter(network=net).count(),
                "route_count": NetworkRoutes.objects.filter(network=net).count(),
            }
        )
    return JsonResponse(data, safe=False)

@login_required
@never_cache
def summary(request):
    members = member_qs(request)
    online_count = sum(1 for m in members if m.is_online())
    data = {
        "members": members.count(),
        "online": online_count,
        "problems": problem_qs(request).count(),
        "networks": network_qs(request).count(),
    }
    return JsonResponse(data)

@login_required
@never_cache
def problems(request):
    data = []
    for p in problem_qs(request).select_related("member", "problem", "member__network"):
        data.append(
            {
                "member": {
                    "member_id": p.member.member_id,
                    "name": p.member.name,
                },
                "problem": p.problem.name if p.problem else None,
                "start_at": p.start_at.isoformat() if p.start_at else None,
                "duration": p.duration,
                "is_done": p.is_done,
                "network": (
                    p.member.network.network_id if p.member.network else None
                ),
            }
        )
    return JsonResponse(data, safe=False)


# ── Network Routes CRUD ──────────────────────────────────────────────────────

def _route_qs(request, network_id):
    """Org-scoped routes queryset for a given network."""
    net = network_qs(request).filter(network_id=network_id).first()
    if not net:
        return None, JsonResponse({"error": "network not found"}, status=404)
    return NetworkRoutes.objects.filter(network=net), None


@login_required
@never_cache
def network_routes_list_create(request, network_id):
    routes_qs, err = _route_qs(request, network_id)
    if err:
        return err

    if request.method == "GET":
        # Pre-fetch members for gateway name resolution — scoped to network
        net = network_qs(request).filter(network_id=network_id).first()
        if not net:
            return JsonResponse({"error": "network not found"}, status=404)
        member_map = {
            m.ipaddress: m.name
            for m in Members.objects.filter(network=net, ipaddress__isnull=False)
        }
        data = []
        for r in routes_qs.select_related("network"):
            gw = r.gateway
            if gw and gw in member_map:
                gw_name = member_map[gw]
            else:
                gw_name = gw  # raw IP or None
            data.append({
                "id": r.id,
                "ip_network": r.ip_network,
                "gateway": gw,
                "gateway_member_name": gw_name,
                "network_id": r.network.network_id,
                "created_at": r.created_at.isoformat() if r.created_at else None,
                "updated_at": r.updated_at.isoformat() if r.updated_at else None,
            })
        return JsonResponse(data, safe=False)

    if request.method == "POST":
        try:
            body = json.loads(request.body)
        except (json.JSONDecodeError, ValueError):
            return JsonResponse({"error": "invalid JSON"}, status=400)

        ip_network = body.get("ip_network", "").strip()
        gateway = body.get("gateway", "").strip() or None

        if not ip_network:
            return JsonResponse({"error": {"ip_network": ["This field is required."]}}, status=400)

        net = network_qs(request).filter(network_id=network_id).first()
        if not net:
            return JsonResponse({"error": "network not found"}, status=404)

        route = NetworkRoutes(ip_network=ip_network, gateway=gateway, network=net)
        # user/organization are required by full_clean but auto-set by save()
        route.user = request.user
        route.organization = request.user.organization
        try:
            route.full_clean()
        except ValidationError as e:
            return JsonResponse({"error": e.message_dict}, status=400)

        route.save()
        return JsonResponse({
            "id": route.id,
            "ip_network": route.ip_network,
            "gateway": route.gateway,
            "network_id": route.network.network_id,
        }, status=201)

    return JsonResponse({"error": "method not allowed"}, status=405)


@login_required
@never_cache
def network_route_detail(request, network_id, ip_network):
    routes_qs, err = _route_qs(request, network_id)
    if err:
        return err

    route = routes_qs.filter(ip_network=ip_network).first()
    if not route:
        return JsonResponse({"error": "route not found"}, status=404)

    if request.method == "GET":
        return JsonResponse({
            "id": route.id,
            "ip_network": route.ip_network,
            "gateway": route.gateway,
            "network_id": route.network.network_id,
            "created_at": route.created_at.isoformat() if route.created_at else None,
            "updated_at": route.updated_at.isoformat() if route.updated_at else None,
        })

    if request.method == "PUT":
        try:
            body = json.loads(request.body)
        except (json.JSONDecodeError, ValueError):
            return JsonResponse({"error": "invalid JSON"}, status=400)

        new_ip_network = body.get("ip_network", route.ip_network).strip()
        new_gateway = body.get("gateway", route.gateway)
        if new_gateway is not None:
            new_gateway = new_gateway.strip() or None

        route.ip_network = new_ip_network
        route.gateway = new_gateway
        try:
            route.full_clean()
        except ValidationError as e:
            return JsonResponse({"error": e.message_dict}, status=400)

        route.save()
        return JsonResponse({
            "id": route.id,
            "ip_network": route.ip_network,
            "gateway": route.gateway,
            "network_id": route.network.network_id,
        })

    if request.method == "DELETE":
        route.delete()
        return JsonResponse({"ok": True}, status=200)

    return JsonResponse({"error": "method not allowed"}, status=405)

@login_required
def ip_loc(request):
    """Return lat/lng for an IP from Redis IPInfo cache. Used by MapPanel polylines."""
    ip = request.GET.get("ip", "").strip()
    if not ip:
        return JsonResponse({"error": "ip parameter required"}, status=400)
    loc = get_ip_loc(ip)
    if loc:
        return JsonResponse({"lat": loc[0], "lng": loc[1]})
    return JsonResponse({"lat": None, "lng": None})

@login_required
@never_cache
def network_detail(request, network_id):
    net = network_qs(request).filter(network_id=network_id).first()
    if not net:
        return JsonResponse({"error": "not found"}, status=404)
    return JsonResponse({
        "network_id": net.network_id,
        "name": net.name,
        "description": net.description,
        "ip_allocation": net.ip_address_networks or "",
        "member_count": Members.objects.filter(network=net).count(),
        "controller_name": net.controller.name if net.controller else None,
    })


@login_required
def network_create(request):
    if request.method != "POST":
        return JsonResponse({"error": "method not allowed"}, status=405)
    try:
        body = json.loads(request.body)
    except (json.JSONDecodeError, ValueError):
        return JsonResponse({"error": "invalid JSON"}, status=400)

    name = body.get("name", "").strip()
    description = body.get("description", "").strip()
    ip_allocation = body.get("ip_allocation", "").strip()

    if not name:
        return JsonResponse({"error": {"name": ["This field is required."]}}, status=400)

    net = Networks(name=name, description=description, ip_address_networks=ip_allocation or None)
    try:
        net.full_clean()
    except ValidationError as e:
        return JsonResponse({"error": e.message_dict}, status=400)

    try:
        net.save()
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=400)

    return JsonResponse({
        "network_id": net.network_id,
        "name": net.name,
        "description": net.description,
        "ip_allocation": net.ip_address_networks or "",
    }, status=201)


@login_required
def network_update(request, network_id):
    if request.method != "PUT":
        return JsonResponse({"error": "method not allowed"}, status=405)
    net = network_qs(request).filter(network_id=network_id).first()
    if not net:
        return JsonResponse({"error": "not found"}, status=404)

    try:
        body = json.loads(request.body)
    except (json.JSONDecodeError, ValueError):
        return JsonResponse({"error": "invalid JSON"}, status=400)

    if "name" in body:
        net.name = body["name"].strip()
    if "description" in body:
        net.description = body["description"].strip()
    if "ip_allocation" in body:
        new_ip = body["ip_allocation"].strip() or None
        if new_ip != (net.ip_address_networks or None):
            return JsonResponse(
                {"error": {"ip_allocation": ["Cannot be changed after creation."]}},
                status=400,
            )

    try:
        net.full_clean()
    except ValidationError as e:
        return JsonResponse({"error": e.message_dict}, status=400)

    try:
        net.save()
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=400)

    return JsonResponse({
        "network_id": net.network_id,
        "name": net.name,
        "description": net.description,
        "ip_allocation": net.ip_address_networks or "",
    })


@login_required
@never_cache
def network_rules(request, network_id):
    """GET/PUT NetworkRules for a network (OneToOne — single rule set per network)."""
    net = network_qs(request).filter(network_id=network_id).first()
    if not net:
        return JsonResponse({"error": "network not found"}, status=404)

    try:
        nr = NetworkRules.objects.get(network=net)
    except NetworkRules.DoesNotExist:
        nr = None

    if request.method == "GET":
        if not nr:
            return JsonResponse({"error": "no rules set"}, status=404)
        return JsonResponse({
            "id": nr.id,
            "name": nr.name,
            "rules_definition": nr.rules_definition,
            "is_block_rule": nr.is_block_rule,
            "network_id": nr.network.network_id,
        })

    if request.method == "PUT":
        try:
            body = json.loads(request.body)
        except (json.JSONDecodeError, ValueError):
            return JsonResponse({"error": "invalid JSON"}, status=400)

        rules_definition = body.get("rules_definition", "").strip()
        is_block_rule = body.get("is_block_rule", False)
        name = body.get("name", "Default Rules").strip()

        if not rules_definition and not is_block_rule:
            return JsonResponse({"error": {"rules_definition": ["Required."]}}, status=400)

        if nr:
            nr.name = name
            nr.rules_definition = rules_definition
            nr.is_block_rule = is_block_rule
        else:
            nr = NetworkRules(name=name, network=net, rules_definition=rules_definition, is_block_rule=is_block_rule)

        try:
            nr.full_clean()
        except ValidationError as e:
            return JsonResponse({"error": e.message_dict}, status=400)

        try:
            nr.save()
        except FileNotFoundError:
            return JsonResponse({"error": "Node.js not installed on server"}, status=400)
        except subprocess.CalledProcessError as e:
            return JsonResponse({"error": f"Rule compilation failed: {e.output}"}, status=400)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)

        return JsonResponse({
            "id": nr.id,
            "name": nr.name,
            "rules_definition": nr.rules_definition,
            "is_block_rule": nr.is_block_rule,
            "network_id": nr.network.network_id,
        })

    return JsonResponse({"error": "method not allowed"}, status=405)



@login_required
@never_cache
def member_peers(request, member_id):
    """Get peers for a member — org-scoped via Members join."""
    member = member_qs(request).filter(member_id=member_id).first()
    if not member:
        return JsonResponse({"error": "member not found"}, status=404)
    peer = MemberPeers.objects.filter(member_id=member_id, network=member.network).first()
    if not peer:
        return JsonResponse({"peers": []})
    try:
        peers_data = json.loads(peer.peers)
    except (json.JSONDecodeError, ValueError):
        peers_data = peer.peers
    return JsonResponse({"peers": peers_data})


@login_required
@never_cache
def monitor_rules(request):
    """Org-scoped MonitorRules CRUD."""
    if request.method == "GET":
        rules = MonitorRules.objects.filter(organization=request.user.organization).select_related("item")
        data = [{
            "id": r.id,
            "name": r.name,
            "item_id": r.item.item_id if r.item else None,
            "item_name": r.item.name if r.item else None,
            "item_threshold": r.item_threshold,
            "created_at": r.created_at.isoformat() if r.created_at else None,
            "updated_at": r.updated_at.isoformat() if r.updated_at else None,
        } for r in rules]
        return JsonResponse(data, safe=False)

    if request.method == "POST":
        try:
            body = json.loads(request.body)
        except (json.JSONDecodeError, ValueError):
            return JsonResponse({"error": "invalid JSON"}, status=400)
        name = body.get("name", "").strip()
        item_id = body.get("item_id", "").strip()
        threshold = body.get("item_threshold", 0)
        if not name or not item_id:
            return JsonResponse({"error": {"name": ["Required."], "item_id": ["Required."]}}, status=400)
        item = MonitorItems.objects.filter(item_id=item_id).first()
        if not item:
            return JsonResponse({"error": {"item_id": ["Invalid item."]}}, status=400)
        rule = MonitorRules(name=name, item=item, item_threshold=threshold)
        try:
            rule.full_clean()
        except ValidationError as e:
            return JsonResponse({"error": e.message_dict}, status=400)
        rule.save()
        return JsonResponse({
            "id": rule.id,
            "name": rule.name,
            "item_id": rule.item.item_id if rule.item else None,
            "item_name": rule.item.name if rule.item else None,
            "item_threshold": rule.item_threshold,
        }, status=201)

    return JsonResponse({"error": "method not allowed"}, status=405)


@login_required
@never_cache
def monitor_rules_detail(request, rule_id):
    """Org-scoped MonitorRules detail/update/delete."""
    rule = MonitorRules.objects.filter(id=rule_id, organization=request.user.organization).first()
    if not rule:
        return JsonResponse({"error": "not found"}, status=404)

    if request.method == "DELETE":
        rule.delete()
        return JsonResponse({"ok": True})

    if request.method == "PUT":
        try:
            body = json.loads(request.body)
        except (json.JSONDecodeError, ValueError):
            return JsonResponse({"error": "invalid JSON"}, status=400)
        if "name" in body:
            rule.name = body["name"].strip()
        if "item_id" in body:
            item = MonitorItems.objects.filter(item_id=body["item_id"].strip()).first()
            if not item:
                return JsonResponse({"error": {"item_id": ["Invalid item."]}}, status=400)
            rule.item = item
        if "item_threshold" in body:
            rule.item_threshold = body["item_threshold"]
        try:
            rule.full_clean()
        except ValidationError as e:
            return JsonResponse({"error": e.message_dict}, status=400)
        rule.save()
        return JsonResponse({
            "id": rule.id,
            "name": rule.name,
            "item_id": rule.item.item_id if rule.item else None,
            "item_name": rule.item.name if rule.item else None,
            "item_threshold": rule.item_threshold,
        })

    return JsonResponse({
        "id": rule.id,
        "name": rule.name,
        "item_id": rule.item.item_id if rule.item else None,
        "item_name": rule.item.name if rule.item else None,
        "item_threshold": rule.item_threshold,
    })


@login_required
@never_cache
def monitor_items(request):
    """Global MonitorItems — GET-only, no org filter."""
    if request.method != "GET":
        return JsonResponse({"error": "method not allowed"}, status=405)
    items = MonitorItems.objects.all()
    data = [{"id": i.id, "name": i.name, "item_id": i.item_id} for i in items]
    return JsonResponse(data, safe=False)


@login_required
@never_cache
def webfilters_list(request):
    """Org-scoped WebFilters list."""
    if request.method != "GET":
        return JsonResponse({"error": "method not allowed"}, status=405)
    filters = WebFilters.objects.filter(organization=request.user.organization)
    data = [{
        "id": wf.id,
        "name": wf.name,
        "description": wf.description,
        "uuid": str(wf.uuid),
        "is_default_block": wf.is_default_block,
        "network_id": wf.network.network_id if wf.network else None,
    } for wf in filters]
    return JsonResponse(data, safe=False)


@login_required
@never_cache
def webfilters_org(request):
    """WebFiltersOrg — get org-to-network mapping, or create."""
    if request.method == "GET":
        org = WebFiltersOrg.objects.filter(organization=request.user.organization).first()
        if not org:
            return JsonResponse({"error": "no mapping set"}, status=404)
        return JsonResponse({
            "id": org.id,
            "organization_id": org.organization.id,
            "network_id": org.network.network_id,
        })
    if request.method == "POST":
        try:
            body = json.loads(request.body)
        except (json.JSONDecodeError, ValueError):
            return JsonResponse({"error": "invalid JSON"}, status=400)
        network_id = body.get("network_id", "").strip()
        if not network_id:
            return JsonResponse({"error": {"network_id": ["Required."]}}, status=400)
        net = network_qs(request).filter(network_id=network_id).first()
        if not net:
            return JsonResponse({"error": "network not found"}, status=404)
        org_obj, _ = WebFiltersOrg.objects.update_or_create(
            organization=request.user.organization,
            defaults={"network": net},
        )
        return JsonResponse({
            "id": org_obj.id,
            "organization_id": org_obj.organization.id,
            "network_id": org_obj.network.network_id,
        }, status=201)
    return JsonResponse({"error": "method not allowed"}, status=405)


@login_required
@never_cache
def webfilters_detail(request, wf_id):
    """WebFilters detail/update/delete — org-scoped."""
    wf = WebFilters.objects.filter(id=wf_id, organization=request.user.organization).first()
    if not wf:
        return JsonResponse({"error": "not found"}, status=404)

    if request.method == "DELETE":
        wf.delete()
        return JsonResponse({"ok": True})

    if request.method == "PUT":
        try:
            body = json.loads(request.body)
        except (json.JSONDecodeError, ValueError):
            return JsonResponse({"error": "invalid JSON"}, status=400)
        if "name" in body:
            wf.name = body["name"].strip()
        if "description" in body:
            wf.description = body["description"].strip()
        if "domains" in body:
            wf.domains = body["domains"].strip()
        if "domains_white" in body:
            wf.domains_white = body["domains_white"].strip()
        if "is_default_block" in body:
            wf.is_default_block = body["is_default_block"]
        try:
            wf.full_clean()
        except ValidationError as e:
            return JsonResponse({"error": e.message_dict}, status=400)
        try:
            wf.save()
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)
        return JsonResponse({
            "id": wf.id,
            "name": wf.name,
            "description": wf.description,
            "uuid": str(wf.uuid),
            "domains": wf.domains,
            "domains_white": wf.domains_white,
            "is_default_block": wf.is_default_block,
        })

    return JsonResponse({
        "id": wf.id,
        "name": wf.name,
        "description": wf.description,
        "uuid": str(wf.uuid),
        "domains": wf.domains,
        "domains_white": wf.domains_white,
        "is_default_block": wf.is_default_block,
    })

@login_required
@never_cache
def webfilters_members_list(request, wf_id):
    """List members assigned to webfilter — org-scoped via webfilter FK."""
    if request.method != "GET":
        return JsonResponse({"error": "method not allowed"}, status=405)
    wf = WebFilters.objects.filter(id=wf_id, organization=request.user.organization).first()
    if not wf:
        return JsonResponse({"error": "not found"}, status=404)
    wfm_qs = WebFiltersMembers.objects.filter(webfilter=wf).select_related("member")
    data = [{
        "id": wfm.id,
        "webfilter_id": wf.id,
        "member_id": wfm.member.id,
        "member_name": wfm.member.name,
        "member_member_id": wfm.member.member_id,
    } for wfm in wfm_qs]
    return JsonResponse(data, safe=False)

@login_required
@never_cache
def webfilters_members_add(request, wf_id):
    """Add member to webfilter — org-scoped via webfilter FK."""
    if request.method != "POST":
        return JsonResponse({"error": "method not allowed"}, status=405)
    wf = WebFilters.objects.filter(id=wf_id, organization=request.user.organization).first()
    if not wf:
        return JsonResponse({"error": "not found"}, status=404)
    try:
        body = json.loads(request.body)
    except (json.JSONDecodeError, ValueError):
        return JsonResponse({"error": "invalid JSON"}, status=400)
    member_id = body.get("member_id")
    if not member_id:
        return JsonResponse({"error": {"member_id": ["Required."]}}, status=400)
    from members.models import Members
    member = Members.objects.filter(id=member_id, organization=request.user.organization).first()
    if not member:
        return JsonResponse({"error": "member not found"}, status=404)
    if WebFiltersMembers.objects.filter(member=member).exists():
        return JsonResponse({"error": "member already assigned to a webfilter"}, status=400)
    wfm = WebFiltersMembers(member=member, webfilter=wf)
    try:
        wfm.save()
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=400)
    return JsonResponse({"ok": True, "member_id": member.id, "webfilter_id": wf.id}, status=201)


@login_required
@never_cache
def webfilters_members_remove(request, wf_id, member_id):
    """Remove member from webfilter — org-scoped via webfilter FK."""
    if request.method != "DELETE":
        return JsonResponse({"error": "method not allowed"}, status=405)
    wf = WebFilters.objects.filter(id=wf_id, organization=request.user.organization).first()
    if not wf:
        return JsonResponse({"error": "not found"}, status=404)
    from members.models import Members
    member = Members.objects.filter(id=member_id, organization=request.user.organization).first()
    if not member:
        return JsonResponse({"error": "member not found"}, status=404)
    wfm = WebFiltersMembers.objects.filter(member=member, webfilter=wf).first()
    if not wfm:
        return JsonResponse({"error": "not found"}, status=404)
    wfm.delete()
    return JsonResponse({"ok": True})

from zabbix.models import ZabbixConfigs


@login_required
@never_cache
def zabbix_configs_list(request):
    """Superuser-only ZabbixConfigs list + create."""
    if not request.user.is_superuser:
        return JsonResponse({"error": "forbidden"}, status=403)
    if request.method == "POST":
        try:
            body = json.loads(request.body)
        except (json.JSONDecodeError, ValueError):
            return JsonResponse({"error": "invalid JSON"}, status=400)
        name = body.get("name", "").strip()
        url = body.get("url", "").strip()
        token = body.get("token", "").strip()
        if not name or not url or not token:
            return JsonResponse({"error": {"name": ["Required."], "url": ["Required."], "token": ["Required."]}}, status=400)
        zc = ZabbixConfigs(name=name, url=url, token=token)
        try:
            zc.full_clean()
        except ValidationError as e:
            return JsonResponse({"error": e.message_dict}, status=400)
        zc.save()
        return JsonResponse({"id": zc.id, "name": zc.name, "url": zc.url, "token": "****"}, status=201)
    data = [{"id": z.id, "name": z.name, "url": z.url, "token": "****"} for z in ZabbixConfigs.objects.all().order_by("-id")]
    return JsonResponse(data, safe=False)


@login_required
@never_cache
def zabbix_configs_detail(request, zc_id):
    """Superuser-only ZabbixConfigs detail/update/delete — token masked, full value on GET."""
    if not request.user.is_superuser:
        return JsonResponse({"error": "forbidden"}, status=403)
    try:
        zc = ZabbixConfigs.objects.get(id=zc_id)
    except ZabbixConfigs.DoesNotExist:
        return JsonResponse({"error": "not found"}, status=404)

    if request.method == "DELETE":
        zc.delete()
        return JsonResponse({"ok": True})

    if request.method == "PUT":
        try:
            body = json.loads(request.body)
        except (json.JSONDecodeError, ValueError):
            return JsonResponse({"error": "invalid JSON"}, status=400)
        if "name" in body:
            zc.name = body["name"].strip()
        if "url" in body:
            zc.url = body["url"].strip()
        if "token" in body:
            new_token = body["token"].strip()
            if new_token and new_token != "****":
                zc.token = new_token
        try:
            zc.full_clean()
        except ValidationError as e:
            return JsonResponse({"error": e.message_dict}, status=400)
        zc.save()
        return JsonResponse({"id": zc.id, "name": zc.name, "url": zc.url, "token": "****"})

    # GET — return full token on detail
    return JsonResponse({"id": zc.id, "name": zc.name, "url": zc.url, "token": zc.token})
from licenses.models import Licenses


@login_required
@never_cache
def licenses_list(request):
    """Superuser-only Licenses list — license_string masked."""
    if not request.user.is_superuser:
        return JsonResponse({"error": "forbidden"}, status=403)
    if request.method != "GET":
        return JsonResponse({"error": "method not allowed"}, status=405)
    licenses = Licenses.objects.all().select_related("organization")
    data = [{
        "id": l.id,
        "node_id": l.node_id,
        "organization_uuid": str(l.organization.uuid) if l.organization else None,
        "is_block_rule": l.is_block_rule,
        "license_string": "****",
        "license_features": l.license_features,
        "created_at": l.created_at.isoformat() if l.created_at else None,
    } for l in licenses]
    return JsonResponse(data, safe=False)
from headscale.models import HS_Users, HS_Nodes, HS_Preauthkeys


@login_required
@never_cache
def headscale_users(request):
    """Org-scoped HS_Users list + create."""
    if request.method == "GET":
        users = HS_Users.objects.filter(organization=request.user.organization)
        data = [{
            "id": u.id,
            "name": u.name,
            "description": u.description,
            "created_at": u.created_at.isoformat() if u.created_at else None,
        } for u in users]
        return JsonResponse(data, safe=False)

    if request.method == "POST":
        try:
            body = json.loads(request.body)
        except (json.JSONDecodeError, ValueError):
            return JsonResponse({"error": "invalid JSON"}, status=400)
        name = body.get("name", "").strip()
        org_id = body.get("organization")
        if not name or not org_id:
            return JsonResponse({"error": {"name": ["Required."], "organization": ["Required."]}}, status=400)
        hs = HS_Users(name=name, description=body.get("description", "").strip(), organization_id=org_id)
        try:
            hs.full_clean()
        except ValidationError as e:
            return JsonResponse({"error": e.message_dict}, status=400)
        try:
            hs.save()
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)
        return JsonResponse({"id": hs.id, "name": hs.name, "description": hs.description}, status=201)

    return JsonResponse({"error": "method not allowed"}, status=405)


@login_required
@never_cache
def headscale_users_detail(request, user_id):
    """Org-scoped HS_Users detail/update/delete."""
    hs = HS_Users.objects.filter(id=user_id, organization=request.user.organization).first()
    if not hs:
        return JsonResponse({"error": "not found"}, status=404)

    if request.method == "DELETE":
        hs.delete()
        return JsonResponse({"ok": True})

    if request.method == "PUT":
        try:
            body = json.loads(request.body)
        except (json.JSONDecodeError, ValueError):
            return JsonResponse({"error": "invalid JSON"}, status=400)
        if "name" in body:
            hs.name = body["name"].strip()
        if "description" in body:
            hs.description = body["description"].strip()
        try:
            hs.full_clean()
        except ValidationError as e:
            return JsonResponse({"error": e.message_dict}, status=400)
        try:
            hs.save()
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)
        return JsonResponse({"id": hs.id, "name": hs.name, "description": hs.description})

    return JsonResponse({"id": hs.id, "name": hs.name, "description": hs.description})


@login_required
@never_cache
def headscale_nodes(request):
    """Org-scoped HS_Nodes list — org auto-set in save()."""
    if request.method != "GET":
        return JsonResponse({"error": "method not allowed"}, status=405)
    nodes = HS_Nodes.objects.filter(organization=request.user.organization)
    data = [{
        "id": n.id,
        "name": n.name,
        "machine_key": n.machine_key,
        "node_key": n.node_key,
        "addresses": n.addresses,
        "created_at": n.created_at.isoformat() if n.created_at else None,
    } for n in nodes]
    return JsonResponse(data, safe=False)


@login_required
@never_cache
def headscale_preauthkeys(request):
    """Org-scoped HS_Preauthkeys list + create."""
    if request.method == "GET":
        keys = HS_Preauthkeys.objects.filter(organization=request.user.organization)
        data = [{
            "id": k.id,
            "key": k.key,
            "is_reusable": k.is_reusable,
            "is_ephemeral": k.is_ephemeral,
            "is_used": k.is_used,
            "hs_user_id": k.hs_user_id,
            "expiration": k.expiration.isoformat() if k.expiration else None,
            "created_at": k.created_at.isoformat() if k.created_at else None,
        } for k in keys]
        return JsonResponse(data, safe=False)

    if request.method == "POST":
        try:
            body = json.loads(request.body)
        except (json.JSONDecodeError, ValueError):
            return JsonResponse({"error": "invalid JSON"}, status=400)
        hs_user_id = body.get("hs_user_id")
        if not hs_user_id:
            return JsonResponse({"error": {"hs_user_id": ["Required."]}}, status=400)
        hs_user = HS_Users.objects.filter(id=hs_user_id, organization=request.user.organization).first()
        if not hs_user:
            return JsonResponse({"error": "HS user not found"}, status=404)
        pk_obj = HS_Preauthkeys(
            hs_user=hs_user,
            is_reusable=body.get("is_reusable", False),
            is_ephemeral=body.get("is_ephemeral", False),
        )
        try:
            pk_obj.full_clean()
        except ValidationError as e:
            return JsonResponse({"error": e.message_dict}, status=400)
        try:
            pk_obj.save()
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)
        return JsonResponse({
            "id": pk_obj.id,
            "key": pk_obj.key,
            "is_reusable": pk_obj.is_reusable,
            "is_ephemeral": pk_obj.is_ephemeral,
            "expiration": pk_obj.expiration.isoformat() if pk_obj.expiration else None,
        }, status=201)

    return JsonResponse({"error": "method not allowed"}, status=405)


@login_required
@never_cache
def headscale_preauthkeys_detail(request, key_id):
    """Org-scoped HS_Preauthkeys detail/delete."""
    pk_obj = HS_Preauthkeys.objects.filter(id=key_id, organization=request.user.organization).first()
    if not pk_obj:
        return JsonResponse({"error": "not found"}, status=404)

    if request.method == "DELETE":
        pk_obj.delete()
        return JsonResponse({"ok": True})

    return JsonResponse({
        "id": pk_obj.id,
        "key": pk_obj.key,
        "is_reusable": pk_obj.is_reusable,
        "is_ephemeral": pk_obj.is_ephemeral,
        "is_used": pk_obj.is_used,
        "expiration": pk_obj.expiration.isoformat() if pk_obj.expiration else None,
    })

def _controller_json(c, mask_token=True):
    """Serialize controller. mask_token=True for list, False for detail GET."""
    return {
        "id": c.id,
        "name": c.name,
        "description": c.description,
        "uri": c.uri,
        "token": "****" if mask_token else c.token,
    }


@login_required
@never_cache
def controllers_list(request):
    if not request.user.is_superuser:
        return JsonResponse({"error": "forbidden"}, status=403)
    if request.method == "POST":
        return controllers_create(request)
    data = [_controller_json(c) for c in Controllers.objects.all().order_by("-id")]
    return JsonResponse(data, safe=False)


def controllers_create(request):
    try:
        body = json.loads(request.body)
    except (json.JSONDecodeError, ValueError):
        return JsonResponse({"error": "invalid JSON"}, status=400)
    name = body.get("name", "").strip()
    uri = body.get("uri", "").strip()
    token = body.get("token", "").strip()
    if not name or not uri or not token:
        return JsonResponse({"error": {"name": ["Required."], "uri": ["Required."], "token": ["Required."]}}, status=400)
    # Validate ZT connection before save
    try:
        zt = Zerotier(uri, token)
        zt.status()
    except Exception as e:
        return JsonResponse({"error": f"Cannot connect to ZeroTier controller: {e}"}, status=400)
    c = Controllers(name=name, description=body.get("description", "").strip(), uri=uri, token=token)
    try:
        c.full_clean()
    except ValidationError as e:
        return JsonResponse({"error": e.message_dict}, status=400)
    try:
        c.save()
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=400)
    return JsonResponse(_controller_json(c), status=201)


@login_required
@never_cache
def controllers_detail(request, controller_id):
    if not request.user.is_superuser:
        return JsonResponse({"error": "forbidden"}, status=403)
    try:
        c = Controllers.objects.get(id=controller_id)
    except Controllers.DoesNotExist:
        return JsonResponse({"error": "not found"}, status=404)

    if request.method == "DELETE":
        c.delete()
        return JsonResponse({"ok": True})

    if request.method == "PUT":
        try:
            body = json.loads(request.body)
        except (json.JSONDecodeError, ValueError):
            return JsonResponse({"error": "invalid JSON"}, status=400)
        if "name" in body:
            c.name = body["name"].strip()
        if "description" in body:
            c.description = body["description"].strip()
        if "uri" in body:
            c.uri = body["uri"].strip()
        if "token" in body:
            new_token = body["token"].strip()
            if new_token and new_token != "****":
                c.token = new_token
        # Validate ZT if uri or token changed
        if "uri" in body or ("token" in body and body.get("token", "").strip() != "****"):
            try:
                zt = Zerotier(c.uri, c.token)
                zt.status()
            except Exception as e:
                return JsonResponse({"error": f"Cannot connect to ZeroTier controller: {e}"}, status=400)
        try:
            c.full_clean()
        except ValidationError as e:
            return JsonResponse({"error": e.message_dict}, status=400)
        try:
            c.save()
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)

    return JsonResponse(_controller_json(c, mask_token=(request.method != "GET")))

def _ot_qs(request):
    """Org-scoped OperationalTime queryset."""
    if request.user.is_superuser:
        return OperationalTime.objects.all()
    return OperationalTime.objects.filter(organization=request.user.organization)


DAY_ENABLED_FIELDS = [
    "is_mon", "is_tue", "is_wed", "is_thu", "is_fri", "is_sat", "is_sun",
]
DAY_TIME_FIELDS = [
    "mon_start", "mon_end", "tue_start", "tue_end", "wed_start", "wed_end",
    "thu_start", "thu_end", "fri_start", "fri_end", "sat_start", "sat_end",
    "sun_start", "sun_end",
]


def _operational_time_json(ot):
    data = {
        "id": ot.id,
        "network_id": ot.network_id,
        "network_name": ot.network.name if ot.network else None,
        "created_at": ot.created_at.isoformat() if ot.created_at else None,
        "updated_at": ot.updated_at.isoformat() if ot.updated_at else None,
    }
    for f in DAY_ENABLED_FIELDS + DAY_TIME_FIELDS:
        data[f] = getattr(ot, f)
    return data


def _apply_ot_body(ot, body):
    """Set day fields from JSON body with type checks. Returns error dict or None."""
    err = {}
    for f in DAY_ENABLED_FIELDS:
        if f in body:
            if not isinstance(body[f], bool):
                err[f] = ["Must be boolean."]
            else:
                setattr(ot, f, body[f])
    for f in DAY_TIME_FIELDS:
        if f in body:
            v = body[f]
            if isinstance(v, bool) or not isinstance(v, int):
                err[f] = ["Must be an integer hour (1-24)."]
            else:
                setattr(ot, f, v)
    return err or None


def _resolve_ot_network(request, body):
    """Resolve + org-scope network_id from body. Returns (network, error)."""
    network_id = str(body.get("network_id", "")).strip()
    if not network_id:
        return None, {"network_id": ["Required."]}
    net = network_qs(request).filter(network_id=network_id).first()
    if net is None:
        return None, {"network_id": ["Not found."]}
    return net, None


@login_required
@never_cache
def operational_times(request):
    """Org-scoped OperationalTime list + create (spec §I /api/app/operational-times/)."""
    if request.method == "GET":
        rows = _ot_qs(request).select_related("network").order_by("id")
        return JsonResponse([_operational_time_json(ot) for ot in rows], safe=False)

    if request.method == "POST":
        try:
            body = json.loads(request.body)
        except (json.JSONDecodeError, ValueError):
            return JsonResponse({"error": "invalid JSON"}, status=400)
        net, err = _resolve_ot_network(request, body)
        if err:
            return JsonResponse({"error": err}, status=400)
        ot = OperationalTime(network=net)
        err = _apply_ot_body(ot, body)
        if err:
            return JsonResponse({"error": err}, status=400)
        try:
            ot.full_clean()
        except ValidationError as e:
            return JsonResponse({"error": e.message_dict}, status=400)
        ot.save()
        return JsonResponse(_operational_time_json(ot), status=201)

    return JsonResponse({"error": "method not allowed"}, status=405)


@login_required
@never_cache
def operational_time_detail(request, ot_id):
    """Org-scoped OperationalTime detail/update/delete."""
    ot = _ot_qs(request).filter(id=ot_id).first()
    if ot is None:
        return JsonResponse({"error": "not found"}, status=404)

    if request.method == "GET":
        return JsonResponse(_operational_time_json(ot))

    if request.method == "DELETE":
        ot.delete()
        return JsonResponse({"ok": True})

    if request.method == "PUT":
        try:
            body = json.loads(request.body)
        except (json.JSONDecodeError, ValueError):
            return JsonResponse({"error": "invalid JSON"}, status=400)
        if "network_id" in body:
            net, err = _resolve_ot_network(request, body)
            if err:
                return JsonResponse({"error": err}, status=400)
            ot.network = net
        err = _apply_ot_body(ot, body)
        if err:
            return JsonResponse({"error": err}, status=400)
        try:
            ot.full_clean()
        except ValidationError as e:
            return JsonResponse({"error": e.message_dict}, status=400)
        ot.save()
        return JsonResponse(_operational_time_json(ot))

    return JsonResponse({"error": "method not allowed"}, status=405)


FEATURES_INT_FIELDS = ["number_of_network", "number_of_member"]
FEATURES_BOOL_FIELDS = [
    "network_multi_ip", "network_rules", "member_multi_ip", "authorize",
    "bridge", "tags", "web", "ssh", "synchronize", "geolocation",
    "online_offline", "is_export", "mobile_connect", "map_dashboard",
    "is_nms", "is_webfilter", "is_webfilter_multinet", "is_dpi",
    "is_telkomsel", "is_deauth_timer", "is_simple_list", "is_lte_signal",
]


def _features_json(f):
    data = {
        "id": f.id,
        "name": f.name,
        "description": f.description,
        "uuid": str(f.uuid),
        "created_at": f.created_at.isoformat() if f.created_at else None,
        "updated_at": f.updated_at.isoformat() if f.updated_at else None,
    }
    for fld in FEATURES_INT_FIELDS + FEATURES_BOOL_FIELDS:
        data[fld] = getattr(f, fld)
    return data


def _apply_features_body(f, body):
    """Set Features fields from JSON body with type checks. Returns error dict or None."""
    err = {}
    for fld in ("name", "description"):
        if fld in body:
            if not isinstance(body[fld], str):
                err[fld] = ["Must be a string."]
            else:
                setattr(f, fld, body[fld].strip())
    for fld in FEATURES_INT_FIELDS:
        if fld in body:
            v = body[fld]
            if isinstance(v, bool) or not isinstance(v, int):
                err[fld] = ["Must be an integer."]
            else:
                setattr(f, fld, v)
    for fld in FEATURES_BOOL_FIELDS:
        if fld in body:
            if not isinstance(body[fld], bool):
                err[fld] = ["Must be boolean."]
            else:
                setattr(f, fld, body[fld])
    return err or None


@login_required
@never_cache
def features_list(request):
    """Superuser-only Features list + create (global license-tier table)."""
    if not request.user.is_superuser:
        return JsonResponse({"error": "forbidden"}, status=403)
    if request.method == "GET":
        rows = Features.objects.all().order_by("id")
        return JsonResponse([_features_json(f) for f in rows], safe=False)

    if request.method == "POST":
        try:
            body = json.loads(request.body)
        except (json.JSONDecodeError, ValueError):
            return JsonResponse({"error": "invalid JSON"}, status=400)
        f = Features()
        err = _apply_features_body(f, body)
        if err:
            return JsonResponse({"error": err}, status=400)
        try:
            f.full_clean()
        except ValidationError as e:
            return JsonResponse({"error": e.message_dict}, status=400)
        f.save()
        return JsonResponse(_features_json(f), status=201)

    return JsonResponse({"error": "method not allowed"}, status=405)


@login_required
@never_cache
def features_detail(request, feature_id):
    """Superuser-only Features detail/update/delete."""
    if not request.user.is_superuser:
        return JsonResponse({"error": "forbidden"}, status=403)
    try:
        f = Features.objects.get(id=feature_id)
    except Features.DoesNotExist:
        return JsonResponse({"error": "not found"}, status=404)

    if request.method == "GET":
        return JsonResponse(_features_json(f))

    if request.method == "DELETE":
        f.delete()  # Organizations.features is SET_NULL — safe
        return JsonResponse({"ok": True})

    if request.method == "PUT":
        try:
            body = json.loads(request.body)
        except (json.JSONDecodeError, ValueError):
            return JsonResponse({"error": "invalid JSON"}, status=400)
        err = _apply_features_body(f, body)
        if err:
            return JsonResponse({"error": err}, status=400)
        try:
            f.full_clean()
        except ValidationError as e:
            return JsonResponse({"error": e.message_dict}, status=400)
        f.save()
        return JsonResponse(_features_json(f))

    return JsonResponse({"error": "method not allowed"}, status=405)


@login_required
@never_cache
def organizations_devices(request):
    """Superuser-only organizations list with nested devices — spec line 34:
    no separate /api/app/devices/ endpoint; devices accessed via organizations."""
    if not request.user.is_superuser:
        return JsonResponse({"error": "forbidden"}, status=403)
    if request.method != "GET":
        return JsonResponse({"error": "method not allowed"}, status=405)
    orgs = Organizations.objects.all().order_by("name").prefetch_related("devices")
    data = [{
        "id": o.id,
        "name": o.name,
        "uuid": str(o.uuid),
        "devices": [{
            "id": d.id,
            "name": d.name,
            "device_id": d.device_id,
            "username": d.username,
            "created_at": d.created_at.isoformat() if d.created_at else None,
            "updated_at": d.updated_at.isoformat() if d.updated_at else None,
        } for d in o.devices.all()],
    } for o in orgs]
    return JsonResponse(data, safe=False)
