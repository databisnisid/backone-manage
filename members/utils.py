from .models import Members
from time import mktime
from django.utils import timezone


def deauthorize_member_offline_at():
    '''
    Deauthorize member which offline_at fields is set 
    and less than current time
    Run every hour at cronjob
    '''

    print('Start - deauthorize_member_offline_at() function')
    members = Members.objects.exclude(offline_at__isnull=True)

    for member in members:
        current_time = timezone.now()
        time_delta = mktime(current_time.timetuple()) - mktime(member.offline_at.timetuple())

        if time_delta > 0:
            print('Deauthorize member {} - {} - {}'.format(member.name, member.member_id, member.offline_at))
            member.is_authorized = False
            member.save()

    print('Fin - deauthorize_member_offline_at() function')

