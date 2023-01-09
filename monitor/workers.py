from django.core.exceptions import ObjectDoesNotExist
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

def check_members_vs_rules(member, mqtt):
    result = []
    rules = MonitorRules.objects.all()
    for rule in rules:
        if rule.item.item_id == 'cpu_usage':
            if is_problem_cpu(mqtt, rule.item.threshold):
                result.append(rule)
        if rule.item.item_id == 'memory_usage':
            if is_problem_memory(mqtt, rule.item.threshold):
                result.append(rule)

    return result


def monitor_members() :
    """
    Monitoring all member via mqtt
    Running every minutes via cronjob
    """

    members = Members.objects.all()

    for member in members:
        try:
            mqtt = Mqtt.objects.get(member_id=member.member_id)
            problems = []
            if ping.ping(member.ipaddress):
                problems = check_members_vs_rules(member, mqtt)
                if problems:
                    for problem in problems:
                        try:
                            member_problem = MemberProblems.objects.get(
                                member=member,
                                problem=problem,
                                is_done=False
                            )
                        except ObjectDoesNotExist:
                            member_problem = MemberProblems()
                            member_problem.member = member
                            member_problem.problem = problem
                            member_problem.mqtt = mqtt
                else:
                    member_problems = MemberProblems.objects.filter(
                        member=member
                    )
                    for member_problem in member_problems:
                        member_problem.is_done = True
                        member_problem.save()

        except ObjectDoesNotExist:
            pass
