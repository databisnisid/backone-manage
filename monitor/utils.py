from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned
from django.utils import timezone
from config.utils import get_cpu_usage
from .models import MonitorRules
#from mqtt.models import Mqtt
#from monitor.models import MonitorRules, OperationalTime
#from connectors.drivers import ping, ssh, mqtt


def compare_values(val1, val2):
    return True if val1 > val2 else False

def is_problem_cpu(mqtt, threshold):
    #load_1, load_5, load_15 = get_cpu_usage(mqtt.uptime, mqtt.num_core)
    load_1, load_5, load_15 = mqtt.get_cpu_usage()
    return compare_values(load_5, threshold)

def is_problem_memory(mqtt, threshold):
    return compare_values(mqtt.memory_usage, threshold)

def is_problem_packet_loss(mqtt, threshold):
    value, is_value = mqtt.get_packet_loss()
    return compare_values(value, threshold)

def is_problem_round_trip(mqtt, threshold):
    value, is_value = mqtt.get_round_trip()
    return compare_values(value, threshold)

check_functions = {
        'cpu_usage': is_problem_cpu,
        'memory_usage': is_problem_memory,
        'packet_loss': is_problem_packet_loss,
        'round_trip': is_problem_round_trip,
        }

item_id_list = ['cpu_usage', 'memory_usage', 'packet_loss', 'round_trip']

def is_problem(member, rule, is_online):
    result = False

    mqtt = None
    if member.mqtt:
        mqtt = member.mqtt

    if is_online:
        if mqtt is not None:
            if rule.item.item_id in item_id_list:
                result = check_functions[rule.item.item_id](mqtt, rule.item_threshold)
            '''
                result = check_functions[rule.item.item_id](mqtt, rule.item_threshold)
            if rule.item.item_id == 'cpu_usage':
                result = check_functions['cpu_usage'](mqtt, rule.item_threshold)
                #result = is_problem_cpu(mqtt, rule.item_threshold)
            if rule.item.item_id == 'memory_usage':
                result = check_functions[rule.item.item_id](mqtt, rule.item_threshold)
                #result = is_problem_memory(mqtt, rule.item_threshold)
            if rule.item.item_id == 'packet_loss':
                result = check_functions[rule.item.item_id](mqtt, rule.item_threshold)
                #result = is_problem_packet_loss(mqtt, rule.item_threshold)
                #result = compare_values(mqtt.packet_loss, rule.item_threshold)
            if rule.item.item_id == 'round_trip':
                result = check_functions[rule.item.item_id](mqtt, rule.item_threshold)
                #result = is_problem_round_trip(mqtt, rule.item_threshold)
                #result = compare_values(mqtt.round_trip, rule.item_threshold)
            '''

    else:
        if rule.item.item_id == 'online_status':
            if member.online_at:
                if timezone.now().date() > member.online_at:
                    result = True
            if member.offline_at:
                if timezone.now() > member.offline_at:
                    result = False


    return result


def check_item_problem(member, item_id):
    is_problem = False
    try:
        monitor_rule = MonitorRules.objects.get(
            item__item_id=item_id,
            organization=member.organization)
    except ObjectDoesNotExist:
        pass
    except MultipleObjectsReturned:
        pass

    if monitor_rule:
        is_problem = check_functions[item_id](
                        member.mqtt, monitor_rule.item_threshold)

    return is_problem

