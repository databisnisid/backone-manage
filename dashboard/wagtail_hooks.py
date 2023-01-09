from django.utils.safestring import mark_safe
from wagtail.admin.ui.components import Component
from wagtail import hooks
from networks.models import Networks, NetworkRoutes
from members.models import Members
from crum import get_current_user
from wagtail.contrib.modeladmin.views import CreateView, EditView
from .summary_panels import *
from django.utils.html import format_html


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
    menu_items[:] = [item for item in menu_items if item.name != 'help']

    if not request.user.organization.features.network_rules:
        menu_items[:] = [item for item in menu_items if item.name != 'network-rules']
    if not request.user.is_superuser:
        menu_items[:] = [item for item in menu_items if item.name != 'memberpeers']
        menu_items[:] = [item for item in menu_items if item.name != 'controllers']

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


@hooks.register('construct_homepage_panels', order=4)
def add_another_welcome_panel(request, panels):
    panels[:] = [panel for panel in panels if panel.name != "site_summary"]
    panels[:] = [panel for panel in panels if panel.name != "workflow_pages_to_moderate"]
    panels[:] = [panel for panel in panels if panel.name != "pages_for_moderation"]
    panels[:] = [panel for panel in panels if panel.name != "user_pages_in_workflow_moderation"]
    panels[:] = [panel for panel in panels if panel.name != "locked_pages"]

    panels.append(NetworksSummaryPanel())
    #panels.append(MembersProblemPanel())
    panels.append(NetworksChartsPanel())
    panels.append(MemberChartsPanel())
    panels.append(ModelChartsPanel())


@hooks.register("insert_global_admin_js", order=100)
def global_admin_js():
    """Add /static/css/custom.js to the admin."""
    return format_html(
        '<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>'
    )
