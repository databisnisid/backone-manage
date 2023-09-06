import random
from django.shortcuts import render
from django.http import JsonResponse
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from .models import Members, Mqtt
from monitor.models import MemberProblems


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
            lat = settings.GEO_WIDGET_DEFAULT_LOCATION['lat'] + random.uniform(-0.005, 0.005)
            lng = settings.GEO_WIDGET_DEFAULT_LOCATION['lng'] + random.uniform(-0.005, 0.005)

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

    return new_members


def get_members_all(request):
    #members = Members.objects.exclude(address__isnull=True, location__isnull=True)
    members = Members.objects.all()
    members_problems = MemberProblems.unsolved.all()
    members_data = prepare_data(members, members_problems)

    return JsonResponse(members_data, safe=False)

def get_members_user(request, user):
    #members = Members.objects.exclude(
    #        address__isnull=True, location__isnull=True
    #        ).filter(user__id=user)
    members = Members.objects.filter(user__id=user)
    members_problems = MemberProblems.unsolved.filter(member__user__id=user)
    members_data = prepare_data(members, members_problems)

    return JsonResponse(members_data, safe=False)

def get_members_org(request, organization):
    #members = Members.objects.exclude(
    #        address__isnull=True, location__isnull=True
    #        ).filter(organization__id=organization)
    members = Members.objects.filter(organization__id=organization)
    members_problems = MemberProblems.unsolved.filter(member__organization__id=organization)
    members_data = prepare_data(members, members_problems)

    return JsonResponse(members_data, safe=False)

