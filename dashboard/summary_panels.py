from wagtail.admin.ui.components import Component
from networks.models import Networks, NetworkRoutes
from members.models import Members
from crum import get_current_user
from random import randint
from django.utils.translation import gettext as _


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

        print(self.networks_name)
        print(self.routes_per_network)

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