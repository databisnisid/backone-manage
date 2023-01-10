from wagtail.admin.ui.components import Component
from django.db.models import Count
from networks.models import Networks, NetworkRoutes
from members.models import Members
from mqtt.models import Mqtt
from crum import get_current_user
from random import randint
from django.utils.translation import gettext as _
from config.utils import to_dictionary
from django.core.exceptions import ObjectDoesNotExist


class NetworksChartsPanel(Component):
    order = 60
    template_name = 'dashboard/networks_charts.html'

    def __init__(self):
        user = get_current_user()
        self.routes_per_network = {}
        self.networks_name = {}
        self.member_per_network = {}
        if user.is_superuser:
            networks = Networks.objects.all()
        elif user.organization.is_no_org:
            networks = Networks.objects.filter(user=user)
        else:
            networks = Networks.objects.filter(organization=user.organization)

        for network in networks:
            self.networks_name[network.network_id] = network.name
            self.routes_per_network[network.network_id] = NetworkRoutes.objects.filter(network=network).count()
            self.member_per_network[network.network_id] = Members.objects.filter(network=network).count()

        #print(self.networks_name)
        #print(self.routes_per_network)

    def get_context_data(self, parent_context):
        context = super().get_context_data(parent_context)
        data_route = []
        data_member = []
        labels = []
        backgroundColor_route = []
        backgroundColor_member = []
        chart_title_route = _('Number of Routes per Network')
        chart_title_member = _('Number of Members per Network')

        for route in self.routes_per_network.values():
            data_route.append(route)
        for member in self.member_per_network.values():
            data_member.append(member)
        for name in self.networks_name.values():
            labels.append(name)
            backgroundColor_route.append('rgba({}, {}, {}, 0.7'.format(
                randint(0, 200), randint(0, 200), 255))
            backgroundColor_member.append('rgba({}, {}, {}, 0.7'.format(
                255, randint(0, 200), randint(0, 200)))

        context['data_route'] = data_route
        context['data_member'] = data_member
        context['labels'] = labels
        context['backgroundColor_route'] = backgroundColor_route
        context['backgroundColor_member'] = backgroundColor_member
        context['chart_title_route'] = chart_title_route
        context['chart_title_member'] = chart_title_member
        #print(context)
        return context


class NetworksSummaryPanel(Component):
    order = 50
    template_name = "dashboard/site_summary.html"

    def __init__(self):
        user = get_current_user()
        if user.is_superuser:
            self.networks = Networks.objects.all().count()
            self.network_routes = NetworkRoutes.objects.all().count()
            self.members = Members.objects.all().count()
        elif user.organization.is_no_org:
            self.networks = Networks.objects.filter(user=user).count()
            self.network_routes = NetworkRoutes.objects.filter(user=user).count()
            self.members = Members.objects.filter(user=user).count()
        else:
            self.networks = Networks.objects.filter(organization=user.organization).count()
            self.network_routes = NetworkRoutes.objects.filter(organization=user.organization).count()
            self.members = Members.objects.filter(organization=user.organization).count()

    def get_context_data(self, parent_context):
        context = super().get_context_data(parent_context)
        context['networks'] = self.networks
        context['network_routes'] = self.network_routes
        context['members'] = self.members

        return context
    '''
    def render_html(self, parent_context):
        return mark_safe("""
        <section class="panel summary nice-padding">
          <h1>Networks: """ + str(self.networks) +
                         """<br />Routes: """ + str(self.network_routes) +
                         """<br />Members: """ + str(self.members) + """</h1>
        </section>
        """)
    '''


class MemberChartsPanel(Component):
    order = 70
    template_name = 'dashboard/members_charts.html'

    def __init__(self):
        user = get_current_user()
        self.member_status = {
            'DIRECT': 0,
            'RELAY': 0,
            'OFFLINE': 0
        }
        self.member_version = {}
        if user.is_superuser:
            members = Members.objects.all()
        elif user.organization.is_no_org:
            members = Members.objects.filter(user=user)
        else:
            members = Members.objects.filter(organization=user.organization)

        for member in members:
            peers = to_dictionary('{}')
            if member.peers:
                peers = to_dictionary(member.peers.peers)

            if 'paths' in peers and len(peers['paths']) != 0:
                version = str(peers['version'])
                latency = peers['latency']
                try:
                    self.member_version['v' + version]
                    self.member_version['v' + version] += 1
                except KeyError:
                    self.member_version['v' + version] = 1

                if latency < 0:
                    self.member_status['RELAY'] += 1
                else:
                    self.member_status['DIRECT'] += 1

            else:
                self.member_status['OFFLINE'] += 1

    def get_context_data(self, parent_context):
        context = super().get_context_data(parent_context)
        data_status = []
        data_version = []
        labels = ['DIRECT', 'RELAY', 'OFFLINE']
        backgroundColor_status = [
            'rgba(46, 125, 50, 0.7)',
            'rgba(21, 101, 192, 0.7)',
            'rgba(198, 40, 40, 0.7)'
        ]
        backgroundColor_version = []

        labels_version = []

        for member in self.member_status.values():
            data_status.append(member)

        for version in self.member_version:
            labels_version.append(version)
            data_version.append(self.member_version[version])
            backgroundColor_version.append('rgba({}, {}, {}, 0.7'.format(
                randint(0, 100), 125, randint(100, 255)))

        is_data_status = False
        is_data_version = False
        if len(data_version) > 0:
            is_data_version = True

        for data in data_version:
            if data > 0:
                is_data_status = True
                break

        context['labels'] = labels
        context['labels_version'] = labels_version
        context['backgroundColor_status'] = backgroundColor_status
        context['backgroundColor_version'] = backgroundColor_version
        context['data_status'] = data_status
        context['data_version'] = data_version
        context['chart_title_status'] = 'Members Status Distribution'
        context['chart_title_version'] = 'Members Version Distribution'
        context['is_data_status'] = is_data_status
        context['is_data_version'] = is_data_version

        return context

class MemberProblemsAnalyticPanel(Component):
    """

    Query total problem  per member
    -------------------------------
    user = get_current_user()
    m = MemberProblemsDone.objects.filter(member__user=user).values('member__name').annotate(count=Count('pk', distinct=True)).order_by('-count')

    m = MemberProblemsDone.objects.filter(member__user=user).order_by('-duration')
    """
    pass

class MembersProblemPanel(Component):
    order = 55
    template_name = "dashboard/members_problem.html"

    def __init__(self):
        self.members_problem = []
        members = Members.objects.all()

        for member in members:
            is_problem = False
            problem_text = []

            if member.is_online():
                '''
                if not member.is_mqtt_online():
                    try:
                        Mqtt.objects.get(member_id=member.member_id)
                        problem_text.append('Inconsistent Online Status')
                        is_problem = True
                    except ObjectDoesNotExist:
                        pass
                '''

                if member.memory_usage() > 50:
                    problem_text.append('High Memory Usage')
                    is_problem = True

                if member.cpu_usage() > 50:
                    problem_text.append('High CPU Usage')
                    is_problem = True

                if is_problem:
                    member.problem_reason = ', '.join(problem_text)
                    self.members_problem.append(member)

    def get_context_data(self, parent_context):
        context = super().get_context_data(parent_context)

        context['members_problem'] = self.members_problem
        return context


class ModelChartsPanel(Component):
    order = 80
    template_name = "dashboard/models_charts.html"

    def __init__(self):
        user = get_current_user()

        if user.is_superuser:
            self.model = (Members.objects.values('mqtt__model').annotate(mcount=Count('mqtt__model')).order_by())
            self.version = (Members.objects.values('mqtt__release_version').annotate(mcount=Count('mqtt__release_version')).order_by())
        elif user.organization.is_no_org:
            self.model = (Members.objects.values('mqtt__model').annotate(mcount=Count('mqtt__model')).filter(user=user).order_by())
            self.version = (Members.objects.values('mqtt__release_version').annotate(mcount=Count('mqtt__release_version')).filter(user=user).order_by())
        else:
            self.model = (Members.objects.values('mqtt__model').annotate(mcount=Count('mqtt__model')).filter(organization=user.organization).order_by())
            self.version = (Members.objects.values('mqtt__release_version').annotate(mcount=Count('mqtt__release_version')).filter(organization=user.organization).order_by())
        #self.model = (Mqtt.objects.values('model').annotate(mcount=Count('model')).order_by())
        #self.version = (Mqtt.objects.values('release_version').annotate(mcount=Count('release_version')).order_by())

    def get_context_data(self, parent_context):
        context = super().get_context_data(parent_context)

        labels_model = []
        data_model = []
        backgroundColor_model = []
        labels_version = []
        data_version = []
        backgroundColor_version = []

        for model in self.model:
            labels_model.append(model['mqtt__model'])
            data_model.append(model['mcount'])
            backgroundColor_model.append('rgba({}, {}, {}, 0.7'.format(
                randint(0, 100), randint(100, 255), 100))

        for version in self.version:
            labels_version.append(version['mqtt__release_version'])
            data_version.append(version['mcount'])
            backgroundColor_version.append('rgba({}, {}, {}, 0.7'.format(
                200, randint(0, 200), randint(200, 255)))

        context['labels_model'] = labels_model
        context['labels_version'] = labels_version
        context['data_model'] = data_model
        context['data_version'] = data_version
        context['backgroundColor_model'] = backgroundColor_model
        context['backgroundColor_version'] = backgroundColor_version
        context['chart_title_model'] = 'Model Distribution'
        context['chart_title_version'] = 'Platform Distribution'
        context['is_data_model'] = True
        context['is_data_version'] = True


        return context

