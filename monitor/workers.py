from django.core.exceptions import ObjectDoesNotExist
#from django.utils import timezone
#from config.utils import get_cpu_usage
#from mqtt.models import Mqtt
from members.models import Members
from monitor.models import MemberProblems, MonitorRules, OperationalTime
from connectors.drivers import ping
from .utils import *


'''
def compare_values(val1, val2):
    return True if val1 > val2 else False

def is_problem_cpu(mqtt, threshold):
    load_1, load_5, load_15 = get_cpu_usage(mqtt.uptime, mqtt.num_core)
    return compare_values(load_5, threshold)

def is_problem_memory(mqtt, threshold):
    return compare_values(mqtt.memory_usage, threshold)

#def is_problem(mqtt, rule):
def is_problem(member, rule, is_online):
    result = False

    mqtt = None
    if member.mqtt:
        mqtt = member.mqtt

    if is_online:
        if mqtt is not None:
            if rule.item.item_id == 'cpu_usage':
                result = is_problem_cpu(mqtt, rule.item_threshold)
            if rule.item.item_id == 'memory_usage':
                result = is_problem_memory(mqtt, rule.item_threshold)
            if rule.item.item_id == 'packet_loss':
                result = compare_values(mqtt.packet_loss, rule.item_threshold)
            if rule.item.item_id == 'round_trip':
                result = compare_values(mqtt.round_trip, rule.item_threshold)

    else:
        if rule.item.item_id == 'online_status':
            if member.online_at:
                if timezone.now().date() > member.online_at:
                    result = True
            if member.offline_at:
                if timezone.now() > member.offline_at:
                    result = False


    return result

'''

def is_operationaltime(member):
    result = False
    try:
        optime = OperationalTime.objects.get(network=member.network)
        currtime = timezone.localtime()
        dayname = currtime.strftime('%a')

        print(dayname)

        if dayname.lower() == 'mon' and optime.is_mon:
            if currtime.hour > optime.mon_start and currtime.hour < optime.mon_end:
                result = True
        if dayname.lower() == 'tue' and optime.is_tue:
            if currtime.hour > optime.tue_start and currtime.hour < optime.tue_end:
                result = True
        if dayname.lower() == 'wed' and optime.is_wed:
            if currtime.hour > optime.wed_start and currtime.hour < optime.wed_end:
                result = True
        if dayname.lower() == 'thu' and optime.is_thu:
            if currtime.hour > optime.thu_start and currtime.hour < optime.thu_end:
                result = True
        if dayname.lower() == 'fri' and optime.is_fri:
            if currtime.hour > optime.fri_start and currtime.hour < optime.fri_end:
                result = True
        if dayname.lower() == 'sat' and optime.is_sat:
            if currtime.hour > optime.sat_start and currtime.hour < optime.sat_end:
                result = True
        if dayname.lower() == 'sun' and optime.is_sun:
            if currtime.hour > optime.sun_start and currtime.hour < optime.sun_end:
                result = True

    except ObjectDoesNotExist:
        result = True
    
    return result


def check_members_vs_rules(member, is_online):
    result = []
    #rules = MonitorRules.objects.all()
    rules = MonitorRules.objects.filter(organization=member.user.organization)
    for rule in rules:
        if is_problem(member, rule, is_online):
            result.append(rule)

    return result


def monitor_members() :
    """
    Monitoring all member via mqtt
    Running every minutes via cronjob
    """

    members = Members.objects.all()

    print("Start", end='')
    for member in members:
        problems = []
        problems_offline = []
        is_solved = True

        if member.ipaddress and is_operationaltime(member):
            if member.is_online() or ping.ping(member.ipaddress):
                print('Checking {} ({})'. format(member.name, member.member_id))
                print("online.", end='')
                problems = check_members_vs_rules(member, True)
            else:
                print(",", end='')
                problems_offline = check_members_vs_rules(member, False)

            for prob in problems_offline:
                problems.append(prob)

            if problems:
                is_solved = False
                for problem in problems:
                    try:
                        member_problem = MemberProblems.unsolved.get(
                            member=member,
                            problem=problem
                        )
                    except ObjectDoesNotExist:
                        member_problem = MemberProblems()
                        member_problem.member = member
                        member_problem.problem = problem
                        #member_problem.mqtt = mqtt

                    member_problem.save()
                    print(".")
                    print('Problem {} ({}) - {}'. format(
                        member.name,
                        member.member_id,
                        problem
                    ))


        if is_solved:
            member_problems = MemberProblems.unsolved.filter(
                member=member
            )
            for member_problem in member_problems:
                member_problem.is_done = True
                member_problem.save()
                print(".")
                print('Solved {} ({}) - {}'. format(
                    member.name,
                    member.member_id,
                    member_problem.problem
                ))

    print(".")
    print("Fin.")
