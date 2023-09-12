from django.core.exceptions import ObjectDoesNotExist
from django.utils import timezone
from config.utils import get_cpu_usage
from mqtt.models import Mqtt
from members.models import Members
from monitor.models import MemberProblems, MonitorRules
from connectors.drivers import ping, ssh, mqtt


def compare_values(val1, val2):
    return True if val1 > val2 else False

def is_problem_cpu(mqtt, threshold):
    load_1, load_5, load_15 = get_cpu_usage(mqtt.uptime, mqtt.num_core)
    return compare_values(load_5, threshold)

def is_problem_memory(mqtt, threshold):
    return compare_values(mqtt.memory_usage, threshold)

#def is_problem(mqtt, rule):
def is_problem(member, rule, is_online):
    mqtt = member.mqtt
    result = False

    if is_online:
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



#def check_members_vs_rules(member, mqtt):
def check_members_vs_rules(member, is_online):
    result = []
    #rules = MonitorRules.objects.all()
    rules = MonitorRules.objects.filter(organization=member.user.organization)
    for rule in rules:
        #if is_problem(member.mqtt, rule):
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
        if member.mqtt:
            #mqtt = Mqtt.objects.get(member_id=member.member_id)
            mqtt = member.mqtt
            problems = []
            is_solved = True
            if member.ipaddress:
                #if member.is_online() and ping.ping(member.ipaddress):
                if member.is_online() or ping.ping(member.ipaddress):
                    #print('Checking {} ({})'. format(member.name, member.member_id))
                    print(".", end='')
                    problems = check_members_vs_rules(member, True)
                else:
                    print(".", end='')
                    problems = check_members_vs_rules(member, False)

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
