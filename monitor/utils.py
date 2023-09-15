from django.core.exceptions import ObjectDoesNotExist
from django.utils import timezone
from config.utils import get_cpu_usage
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

'''

def is_operationaltime(member):
    result = False
    try:
        optime = OperationalTime.objects.get(network=member.network)
        currtime = timezone.localtime()
        dayname = currtime.strftime('%a')

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
    rules = MonitorRules.objects.filter(organization=member.user.organization)
    for rule in rules:
        if is_problem(member, rule, is_online):
            result.append(rule)

    return result
'''