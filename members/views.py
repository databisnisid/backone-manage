import random
from django.shortcuts import render
from django.http import JsonResponse
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.utils import timezone
from .models import Members, Mqtt
from monitor.models import MemberProblems


def randomize_coordinate(members):
    for i in range(0, len(members)):
        for j in range(i+1, len(members)):
            if members[i]['lat'] == members[j]['lat'] and members[i]['lng'] == members[j]['lng']:
                members[i]['lat'] = str(float(members[i]['lat']) + random.uniform(-0.001, 0.001))
                members[i]['lng'] = str(float(members[i]['lng']) + random.uniform(-0.001, 0.001))
                print(member[i]['lat'], member[i]['lng'])


def is_problem(member, members_problems):
    is_found = 0
    for problem in members_problems:
        if member.id == problem.member.id:
            is_found = 1
            break

    return is_found


def prepare_data(members, members_problems):
    new_members = []

    for member in members:
        member_geo = {}
        try:
            point = member.location.split(';')
            result = point[1].split(' ')
            lng = result[0].replace('POINT(', '')
            lat = result[1].replace(')', '')
        except AttributeError:
            lat = settings.GEO_WIDGET_DEFAULT_LOCATION['lat'] + random.uniform(-0.0025, 0.0025)
            lng = settings.GEO_WIDGET_DEFAULT_LOCATION['lng'] + random.uniform(-0.0025, 0.0025)

        member_geo['id'] = member.id
        member_geo['name'] = member.name
        member_geo['member_id'] = member.member_id
        member_geo['address'] = member.address
        member_geo['ipaddress'] = member.ipaddress
        member_geo['lat'] = lat
        member_geo['lng'] = lng
        member_geo['is_online'] = 1 if member.is_online() else 0
        member_geo['is_problem'] = is_problem(member, members_problems)
        new_members.append(member_geo)

    #return new_members
    return randomize_coordinate(new_members)


def problem_time():
    return timezone.now() - timezone.timedelta(seconds=settings.MONITOR_DELAY)


def get_members_all(request):
    members = Members.objects.all()
    members_problems = MemberProblems.unsolved.filter(start_at__lt=problem_time())
    members_data = prepare_data(members, members_problems)

    return JsonResponse(members_data, safe=False)


def get_members_user(request, user):
    members = Members.objects.filter(user__id=user)
    members_problems = MemberProblems.unsolved.filter(
            member__user__id=user, start_at__lt=problem_time()
            )
    members_data = prepare_data(members, members_problems)

    return JsonResponse(members_data, safe=False)


def get_members_org(request, organization):
    members = Members.objects.filter(organization__id=organization)
    members_problems = MemberProblems.unsolved.filter(
            member__organization__id=organization, start_at__lt=problem_time()
            )
    members_data = prepare_data(members, members_problems)

    return JsonResponse(members_data, safe=False)

