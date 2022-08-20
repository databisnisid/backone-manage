import ast
import json
from crum import get_current_user
#from django.contrib.auth.models import User
from accounts.models import User
from django.core.exceptions import ObjectDoesNotExist


def to_json(data):
    return json.loads(data.replace("\'", "\""))


def to_dictionary(data):
    return ast.literal_eval(data.replace("\'", "\""))


def to_list(data):
    result = []
    for d in data:
        result.append(d)
    return result


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
