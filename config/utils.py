import ast
from crum import get_current_user
from django.contrib.auth.models import User


def to_dictionary(data):
    return ast.literal_eval(data.replace("\'", "\""))


def to_list(data):
    result = []
    for d in data:
        result.append(d)
    return result


def get_user():
    user = get_current_user()
    if user:
        return user
    else:
        user = User.objects.get(id=1)
        return user
