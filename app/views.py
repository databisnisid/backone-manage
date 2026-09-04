from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.conf import settings
from django.views.decorators.cache import never_cache

from members.models import Members
from members.views import prepare_data
from networks.models import Networks
from problems.models import MemberProblems
from mqtt.models import Mqtt


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
    """Parse `name;POINT(lng lat)` (Wagtail GeoWidget) → (lat, lng) floats; (None, None) if absent."""
    if not location:
        return None, None
    try:
        point = location.split(";")
        result = point[1].split(" ")
        lng = float(result[0].replace("POINT(", ""))
        lat = float(result[1].replace(")", ""))
    except (IndexError, ValueError, AttributeError):
        return None, None
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
        if real_lat is not None and real_lng is not None:
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