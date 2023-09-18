import ast
import json
from crum import get_current_user
#from django.contrib.auth.models import User
from accounts.models import User
from django.core.exceptions import ObjectDoesNotExist
from django.utils import timezone

'''
from django.http import HttpRequest


def get_lockout_parameters(request_or_attempt, credentials):

    if isinstance(request_or_attempt, HttpRequest):
       is_localhost = request.META.get("REMOTE_ADDR") == "127.0.0.1"

    else:
        is_localhost = request_or_attempt.ip_address == "127.0.0.1"

    if is_localhost:
       return ["username"]

    return ["ip_address", "username"]
'''


def to_json(data):
    return json.loads(data.replace("\'", "\""))


def to_dictionary(data):
    if type(data) is not dict:
        return ast.literal_eval(data.replace("\'", "\""))
    else:
        return data


def to_list(data):
    result = []
    for d in data:
        result.append(d)
    return result


def calculate_bandwidth_unit(value):
    bandwidth_unit = 'B'
    if value > 1024:
        value = value / 1024
        bandwidth_unit = 'KB'

    if value > 1024:
        value = value / 1024
        bandwidth_unit = 'MB'

    if value > 1024:
        value = value / 1024
        bandwidth_unit = 'GB'

    if value > 1024:
        value = value / 1024
        bandwidth_unit = 'TB'

    return bandwidth_unit, value



def get_user():
    user = get_current_user()

    #if user is None:
    if user is None or user.id is None:
        print('Here!!! ', user)
        try:
            #pass
            user = User.objects.get(id=1)
        except ObjectDoesNotExist:
            user = None

    return user


def get_string_between(start, end, s):
    if s is None:
        return ''
    else:
        return s[s.find(start)+len(start):s.rfind(end)]


def get_load_string(uptime_string):
    start = 'average: '
    end = ''
    return get_string_between(start, end, uptime_string)


def get_uptime_string(uptime_string):
    start = 'up '
    end = ', load average:'
    return get_string_between(start, end, uptime_string)


def get_cpu_usage(string, cpu):
    load = get_load_string(string)
    if load:
        load_split = load.split(',')
        return float(load_split[0])/cpu*100, float(load_split[1])/cpu*100, float(load_split[2])/cpu*100
    else:
        return 0, 0, 0


def readable_timedelta(last_online):
    now = timezone.now()
    duration = now - timezone.localtime(last_online)
    data = {}
    data['days'], remaining = divmod(duration.total_seconds(), 86400)
    data['hours'], remaining = divmod(remaining, 3600)
    data['minutes'], data['seconds'] = divmod(remaining, 60)

    time_parts = ((name, round(value)) for name, value in data.items())
    time_parts = [f'{value} {name[:-1] if value == 1 else name}' for name, value in time_parts if value > 0]
    if time_parts:
        return ' '.join(time_parts)
    else:
        return 'below 1 second'

def readable_timedelta_seconds(seconds):
    data = {}
    data['days'], remaining = divmod(seconds, 86400)
    data['hours'], remaining = divmod(remaining, 3600)
    data['minutes'], data['seconds'] = divmod(remaining, 60)

    time_parts = ((name, round(value)) for name, value in data.items())
    time_parts = [f'{value} {name[:-1] if value == 1 else name}' for name, value in time_parts if value > 0]
    if time_parts:
        return ' '.join(time_parts)
    else:
        return 'below 1 second'

