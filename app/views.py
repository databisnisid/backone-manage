import json
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.conf import settings
from django.views.decorators.cache import never_cache
from django.core.exceptions import ValidationError

from members.models import Members
from members.views import prepare_data
from networks.models import Networks, NetworkRoutes
from problems.models import MemberProblems
from mqtt.models import Mqtt
from connectors.redis_ipinfo import get_ip_loc


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
                "member_count": Members.objects.filter(network=net).count(),
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
        data = []
        for r in routes_qs.select_related("network"):
            data.append({
                "id": r.id,
                "ip_network": r.ip_network,
                "gateway": r.gateway,
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
        net.ip_address_networks = body["ip_allocation"].strip() or None

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
