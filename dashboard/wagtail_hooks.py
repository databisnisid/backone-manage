from django.utils.safestring import mark_safe
from wagtail.admin.ui.components import Component
from wagtail import hooks
from networks.models import Networks, NetworkRoutes
from members.models import Members
from crum import get_current_user


@hooks.register('construct_reports_menu')
def hide_reports_menu_item(request, menu_items):
    menu_items[:] = [item for item in menu_items if item.name != 'workflows']
    menu_items[:] = [item for item in menu_items if item.name != 'workflow-tasks']
    menu_items[:] = [item for item in menu_items if item.name != 'aging-pages']
    menu_items[:] = [item for item in menu_items if item.name != 'locked-pages']


@hooks.register('construct_main_menu')
def hide_snippets_menu_item(request, menu_items):
    menu_items[:] = [item for item in menu_items if item.name != 'documents']
    menu_items[:] = [item for item in menu_items if item.name != 'explorer']
    menu_items[:] = [item for item in menu_items if item.name != 'images']


@hooks.register("construct_settings_menu")
def hide_user_menu_item(request, menu_items):
    menu_items[:] = [item for item in menu_items if item.name != "workflows"]
    menu_items[:] = [item for item in menu_items if item.name != "workflow-tasks"]
    menu_items[:] = [item for item in menu_items if item.name != "redirects"]
    menu_items[:] = [item for item in menu_items if item.name != "sites"]
    menu_items[:] = [item for item in menu_items if item.name != "collections"]


class NetworksSummaryPanel(Component):
    order = 50

    def __init__(self):
        user = get_current_user()
        self.networks = Networks.objects.filter(user=user).count()
        self.network_routes = NetworkRoutes.objects.filter(user=user).count()
        self.members = Members.objects.filter(user=user).count()

    def render_html(self, parent_context):
        return mark_safe("""
        <section class="panel summary nice-padding">
          <h1>Networks: """ + str(self.networks) +
                         """<br />Routes: """ + str(self.network_routes) +
                         """<br />Members: """ + str(self.members) + """</h1>
        </section>
        """)


@hooks.register('construct_homepage_panels')
def add_another_welcome_panel(request, panels):
    panels[:] = [panel for panel in panels if panel.name != "site_summary"]
    panels[:] = [panel for panel in panels if panel.name != "workflow_pages_to_moderate"]
    panels[:] = [panel for panel in panels if panel.name != "pages_for_moderation"]
    panels[:] = [panel for panel in panels if panel.name != "user_pages_in_workflow_moderation"]
    panels[:] = [panel for panel in panels if panel.name != "locked_pages"]

    panels.append(NetworksSummaryPanel())
