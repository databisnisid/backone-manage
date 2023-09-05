from django.shortcuts import render
from django.http import JsonResponse
from django.core.exceptions import ObjectDoesNotExist
from .models import Members, Mqtt


def prepare_data(members):
    new_members = []

    for member in members:
        member_geo = {}
        point = member.location.split(';')
        result = point[1].split(' ')
        lng = result[0].replace('POINT(', '')
        lat = result[1].replace(')', '')
        member_geo['name'] = member.name
        member_geo['member_id'] = member.member_id
        member_geo['address'] = member.address
        member_geo['ipaddress'] = member.ipaddress
        member_geo['lat'] = lat
        member_geo['lng'] = lng
        member_geo['is_online'] = 1 if member.is_online() else 0
        new_members.append(member_geo)

    return new_members


def get_members_all(request):
    members = Members.objects.exclude(address__isnull=True, location__isnull=True)
    members_data = prepare_data(members)

    return JsonResponse(members_data, safe=False)

def get_members_user(request, user):
    members = Members.objects.exclude(address__isnull=True, location__isnull=True).filter(user__id=user)
    members_data = prepare_data(members)

    return JsonResponse(members_data, safe=False)

def get_members_org(request, organization):
    members = Members.objects.exclude(address__isnull=True, location__isnull=True).filter(organization__id=organization)
    members_data = prepare_data(members)

    return JsonResponse(members_data, safe=False)





# Create your views here.
