from .models import Members
from time import mktime
from django.utils import timezone
from django.conf import settings


def get_unique_members(members):
    members_unique = []
    member_id_list = []


    for member in members:
        if member.member_id not in member_id_list:
            members_unique.append(member)
            member_id_list.append(member.member_id)
    
    return members_unique


def deauthorize_member_offline_at():
    '''
    Deauthorize member which offline_at fields is set 
    and less than current time
    Run every hour at cronjob
    '''

    print(timezone.localtime(), 'START - deauthorize_member_offline_at() function')
    members = Members.objects.exclude(
            offline_at__isnull=True
            )

    for member in members:
        current_time = timezone.now()
        time_delta = mktime(current_time.timetuple()) - mktime(member.offline_at.timetuple())

        #if time_delta > 0:
        if time_delta > 0 and member.is_authorized:
            print('Deauthorize member {} - {} - {} - {}'.format(member.name, member.member_id, member.offline_at, time_delta))
            member.is_authorized = False
            member.save()

        '''
        Delete member base on MEMBER_DELETE_PERIOD
        if time_delta > (settings.MEMBER_DELETE_PERIOD * 24 * 3600):
            print('Delete member {} - {} - {} - {}'.format(member.name, member.member_id, member.offline_at, time_delta))
            member.delete()
        '''

    print(timezone.localtime(), 'DONE - deauthorize_member_offline_at() function')

