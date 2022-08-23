from django.utils.safestring import mark_safe
from wagtail.admin.ui.components import Component
from wagtail import hooks
from networks.models import Networks, NetworkRoutes
from members.models import Members
from crum import get_current_user
from wagtail.contrib.modeladmin.views import CreateView, EditView


#@hooks.register("insert_global_admin_css", order=100)
#def global_admin_css():
#    """Workaround wagtail issue 7210
#    https://github.com/wagtail/wagtail/issues/7210
#    """
#    return "<style>textarea {resize:vertical !important}</style>"


@hooks.register('construct_reports_menu', order=1)
def hide_reports_menu_item(request, menu_items):
    menu_items[:] = [item for item in menu_items if item.name != 'workflows']
    menu_items[:] = [item for item in menu_items if item.name != 'workflow-tasks']
    menu_items[:] = [item for item in menu_items if item.name != 'aging-pages']
    menu_items[:] = [item for item in menu_items if item.name != 'locked-pages']
    #pass


@hooks.register('construct_main_menu', order=2)
def hide_snippets_menu_item(request, menu_items):
    menu_items[:] = [item for item in menu_items if item.name != 'documents']
    menu_items[:] = [item for item in menu_items if item.name != 'explorer']
    menu_items[:] = [item for item in menu_items if item.name != 'images']

    if not request.user.organization.features.network_rules:
        menu_items[:] = [item for item in menu_items if item.name != 'network-rules']
    if not request.user.is_superuser:
        menu_items[:] = [item for item in menu_items if item.name != 'memberpeers']

    #for panel in menu_items:
    #    print(panel.name)


@hooks.register("construct_settings_menu", order=3)
def hide_user_menu_item(request, menu_items):
    menu_items[:] = [item for item in menu_items if item.name != "workflows"]
    menu_items[:] = [item for item in menu_items if item.name != "workflow-tasks"]
    menu_items[:] = [item for item in menu_items if item.name != "redirects"]
    menu_items[:] = [item for item in menu_items if item.name != "sites"]
    menu_items[:] = [item for item in menu_items if item.name != "collections"]
    #pass


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


@hooks.register('construct_homepage_panels', order=4)
def add_another_welcome_panel(request, panels):
    panels[:] = [panel for panel in panels if panel.name != "site_summary"]
    panels[:] = [panel for panel in panels if panel.name != "workflow_pages_to_moderate"]
    panels[:] = [panel for panel in panels if panel.name != "pages_for_moderation"]
    panels[:] = [panel for panel in panels if panel.name != "user_pages_in_workflow_moderation"]
    panels[:] = [panel for panel in panels if panel.name != "locked_pages"]

    panels.append(NetworksSummaryPanel())
