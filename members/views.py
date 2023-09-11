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
                #print('Before', members[i]['lat'], members[i]['lng'])
                members[i]['lat'] = float(members[i]['lat']) + random.uniform(-0.0001, 0.0001)
                members[i]['lng'] = float(members[i]['lng']) + random.uniform(-0.0001, 0.0001)
                #print('After', members[i]['lat'], members[i]['lng'])

    return members


def is_problem(member, members_problems):
    is_found = 0
    problem_string = ''
    for problem in members_problems:
        if member.id == problem.member.id:
            is_found = 1
            problem_string = problem.problem.name
            break

    return is_found, problem_string


def is_new(timestamp):
    timedelta = timezone.now() - timestamp

    #print(timedelta.days)
    if timedelta.days > settings.MEMBER_NEW_DAY:
        return False
    else:
        return True


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
        is_found, problem_string = is_problem(member, members_problems)
        #member_geo['is_problem'] = is_problem(member, members_problems)
        member_geo['is_problem'] = is_found
        member_geo['problem_string'] = problem_string
        #member_geo['created_at'] = member.created_at.strftime('%s')
        member_geo['is_new'] = 1 if is_new(member.created_at) else 0 
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

