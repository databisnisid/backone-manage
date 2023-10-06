from django.core.exceptions import ObjectDoesNotExist
#from django.utils import timezone
#from config.utils import get_cpu_usage
#from mqtt.models import Mqtt
from members.models import Members
from monitor.models import MonitorRules, OperationalTime
from problems.models import MemberProblems
from connectors.drivers import ping
from .utils import is_operationaltime, check_members_vs_rules


def check_member_problem(member):
    pass
    problems = []
    problems_offline = []
    is_solved = True

    if member.ipaddress and is_operationaltime(member):
        if member.is_online() or ping.ping(member.ipaddress):
            print('Checking Online {} ({})'. format(member.name, member.member_id))
            print(".", end='')
            problems = check_members_vs_rules(member, True)
        else:
            print('Checking Offline {} ({})'. format(member.name, member.member_id))
            print(",", end='')
            problems_offline = check_members_vs_rules(member, False)

        for prob in problems_offline:
            problems.append(prob)

        if problems:
            is_solved = False
            ''' Write Code to remove solved Problem '''
            ''' Code here '''
            member_problems_all = MemberProblems.unsolved.filter(
                    member=member
                    )

            for problem in problems:
                try:
                    member_problem = MemberProblems.unsolved.get(
                        member=member,
                        problem=problem
                    )
                    ''' Find solved problem '''
                    member_problems_all = member_problems_all.difference(member_problem)
                except ObjectDoesNotExist:
                    member_problem = MemberProblems()
                    member_problem.member = member
                    member_problem.problem = problem
                    #member_problem.mqtt = mqtt

                    member_problem.save()
                except AttributeError:
                    pass

                print(".")
                print('Problem {} ({}) - {}'. format(
                    member.name,
                    member.member_id,
                    problem
                ))

            ''' Solved Problems Test '''
            for member_problem_solved in member_problems_all:
                member_problem_solved.is_done = True
                member_problem_solved.save()
                print(".")
                print('Solved {} ({}) - {}'. format(
                    member.name,
                    member.member_id,
                    member_problem_solved.problem
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


def monitor_members() :
    """
    Monitoring all member via mqtt
    Running every minutes via cronjob
    """

    members = Members.objects.all()

    print("Start", end='')
    for member in members:
        check_member_problem(member)

    print(".")
    print("Fin.")
