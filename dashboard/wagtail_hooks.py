# from django.http import HttpRequest
# from django.utils.safestring import mark_safe
# from django.templatetags.static import static

# from wagtail.admin.ui.components import Component
from wagtail import hooks

# from networks.models import Networks, NetworkRoutes
# from members.models import Members
# from crum import get_current_user
# from wagtail.contrib.modeladmin.views import CreateView, EditView
from .summary_panels import *
from .statistic_panels import ProvidersChart
from django.utils.html import format_html
from django.utils.translation import gettext as _
from axes.models import AccessAttempt, AccessLog, AccessFailureLog
from wagtail.snippets.models import register_snippet
from wagtail.snippets.views.snippets import SnippetViewSet, SnippetViewSetGroup
from django.conf import settings
from licenses.utils import is_license_valid


# @hooks.register("insert_global_admin_css", order=100)
# def global_admin_css():
#    """Workaround wagtail issue 7210
#    https://github.com/wagtail/wagtail/issues/7210
#    """
#    return "<style>textarea {resize:vertical !important}</style>"


"""
@hooks.register("insert_global_admin_css")
def global_admin_css():
    return format_html(
        '<link rel="stylesheet" href="{}">', static("dashboard/css/custom.css")
    )
"""


@hooks.register("construct_reports_menu", order=1)
def hide_reports_menu_item(request, menu_items):
    menu_items[:] = [item for item in menu_items if item.name != "workflows"]
    menu_items[:] = [item for item in menu_items if item.name != "workflow-tasks"]
    menu_items[:] = [item for item in menu_items if item.name != "aging-pages"]
    menu_items[:] = [item for item in menu_items if item.name != "locked-pages"]


@hooks.register("construct_main_menu", order=2)
def hide_snippets_menu_item(request, menu_items):
    menu_items[:] = [item for item in menu_items if item.name != "documents"]
    menu_items[:] = [item for item in menu_items if item.name != "explorer"]
    menu_items[:] = [item for item in menu_items if item.name != "images"]
    menu_items[:] = [item for item in menu_items if item.name != "help"]

    if not request.user.is_superuser:
        if not request.user.organization.features.is_nms:
            menu_items[:] = [item for item in menu_items if item.name != "monitor"]

    if not request.user.is_superuser:
        if not request.user.organization.features.network_rules:
            menu_items[:] = [
                item for item in menu_items if item.name != "network-rules"
            ]

    if not request.user.is_superuser:
        if not request.user.organization.features.is_webfilter:
            menu_items[:] = [item for item in menu_items if item.name != "waf"]
            # menu_items[:] = [item for item in menu_items if item.name != 'webfilters']

    if not request.user.is_superuser:
        menu_items[:] = [item for item in menu_items if item.name != "memberpeers"]
        menu_items[:] = [item for item in menu_items if item.name != "controllers"]
        menu_items[:] = [item for item in menu_items if item.name != "backone-hs"]

    if settings.HEADSCALE_ON == 0:
        menu_items[:] = [item for item in menu_items if item.name != "backone-hs"]

    """
    License
    """
    """
    try:
        lic = Licenses.objects.get(id=1)
        lic_status, lic_day = lic.check_license()

    except ObjectDoesNotExist:
        lic_status = False

    if not lic_status:
        menu_items[:] = [item for item in menu_items if item.name != 'monitor']
        menu_items[:] = [item for item in menu_items if item.name != 'waf']
        menu_items[:] = [item for item in menu_items if item.name != 'members']
        menu_items[:] = [item for item in menu_items if item.name != 'networks']
        menu_items[:] = [item for item in menu_items if item.name != 'network-routes']
        menu_items[:] = [item for item in menu_items if item.name != 'network-rules']
        menu_items[:] = [item for item in menu_items if item.name != 'mqtt']
        menu_items[:] = [item for item in menu_items if item.name != 'memberpeers']
        menu_items[:] = [item for item in menu_items if item.name != 'controllers']
        menu_items[:] = [item for item in menu_items if item.name != 'backone-hs']
    """


@hooks.register("construct_settings_menu", order=3)
def hide_user_menu_item(request, menu_items):
    menu_items[:] = [item for item in menu_items if item.name != "workflows"]
    menu_items[:] = [item for item in menu_items if item.name != "workflow-tasks"]
    menu_items[:] = [item for item in menu_items if item.name != "redirects"]
    # menu_items[:] = [item for item in menu_items if item.name != "sites"]
    menu_items[:] = [item for item in menu_items if item.name != "collections"]


@hooks.register("construct_homepage_panels", order=4)
def add_another_welcome_panel(request, panels):
    panels[:] = [panel for panel in panels if panel.name != "site_summary"]
    panels[:] = [
        panel for panel in panels if panel.name != "workflow_pages_to_moderate"
    ]
    panels[:] = [panel for panel in panels if panel.name != "pages_for_moderation"]
    panels[:] = [
        panel for panel in panels if panel.name != "user_pages_in_workflow_moderation"
    ]
    panels[:] = [panel for panel in panels if panel.name != "locked_pages"]

    """
    License
    """
    """
    try:
        lic = Licenses.objects.get(id=1)
        lic_status, lic_day = lic.check_license()

    except ObjectDoesNotExist:
        lic_status = False
    """
    lic_status = True

    # if request.user.is_superuser and lic_status:
    panels.append(LicenseSummaryPanel())
    if request.user.is_superuser:
        panels.append(MapSummaryPanel())
    # elif not request.user.is_anonymous:
    elif request.user.organization.features.map_dashboard and is_license_valid(
        request.user
    ):
        panels.append(MapSummaryPanel())

    # panels.append(NetworksSummaryPanel())
    # panels.append(MembersProblemPanel())
    panels.append(MemberChartsPanel())
    panels.append(ModelChartsPanel())
    if request.user.is_superuser:
        panels.append(NetworksChartsPanel())
    if request.user.organization.features.number_of_network > 1:
        panels.append(NetworksChartsPanel())
    if request.user.is_superuser or request.user.has_perm("licenses.change_licenses"):
        panels.append(LicenseDecoderPanel())

    # Testing Ping Summary Panel
    # if request.user.is_superuser:
    #   panels.append(PingSummaryPanel())

    # Testing Providers Distribution Panel
    # if request.user.is_superuser:
    #    panels.append(ProvidersChart())


@hooks.register("insert_global_admin_js", order=100)
def global_admin_js():
    """Add /static/css/custom.js to the admin."""
    return format_html('<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>')


"""
@hooks.register('construct_snippet_listing_buttons')
def remove_snippet_add_button_item(buttons, snippet, user, context=None):
    for button in buttons:
        index = buttons.index(button)

        if 'add' in button.label.lower():
            buttons.pop(index)
            break
"""


class AccessAttemptSVS(SnippetViewSet):
    model = AccessAttempt
    menu_label = _("Access Attempt")
    icon = "lock-open"
    inspect_view_enabled = True
    # index_template_name = 'dashboard/snippets/index.html'

    exclude_from_explorer = False

    add_to_admin_menu = False

    list_display = [
        "attempt_time",
        "ip_address",
        "user_agent",
        "username",
        "path_info",
        "failures_since_start",
    ]
    list_filter = ["attempt_time", "path_info"]
    search_fields = ["ip_address", "username", "user_agent", "path_info"]
    date_hierarchy = "attempt_time"

    readonly_fields = [
        "user_agent",
        "ip_address",
        "username",
        "http_accept",
        "path_info",
        "attempt_time",
        "get_data",
        "post_data",
        "failures_since_start",
    ]

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        queryset = self.model.objects.all()
        queryset = queryset.exclude(username="backone")

        return queryset


class AccessLogSVS(SnippetViewSet):
    model = AccessLog
    menu_label = _("Access Log")
    icon = "list-ul"
    # index_template_name = 'dashboard/snippets/index.html'

    exclude_from_explorer = False

    add_to_admin_menu = False

    list_display = [
        "attempt_time",
        "logout_time",
        "ip_address",
        "username",
        "user_agent",
        "path_info",
    ]
    list_filter = ["attempt_time", "path_info"]
    search_fields = ["ip_address", "username", "user_agent", "path_info"]
    date_hierarchy = "attempt_time"

    readonly_fields = [
        "user_agent",
        "ip_address",
        "username",
        "http_accept",
        "path_info",
        "attempt_time",
        "logout_time",
    ]

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        queryset = self.model.objects.all()
        queryset = queryset.exclude(username="backone")

        return queryset


class AccessFailureLogSVS(SnippetViewSet):
    model = AccessFailureLog
    menu_label = _("Access Failure")
    icon = "chain-broken"
    # index_template_name = 'dashboard/snippets/index.html'

    exclude_from_explorer = False

    add_to_admin_menu = False

    list_display = [
        "attempt_time",
        "ip_address",
        "username",
        "user_agent",
        "path_info",
        "locked_out",
    ]
    list_filter = ["attempt_time", "path_info"]
    search_fields = ["ip_address", "username", "user_agent", "path_info"]
    date_hierarchy = "attempt_time"

    readonly_fields = [
        "user_agent",
        "ip_address",
        "username",
        "http_accept",
        "path_info",
        "attempt_time",
        "locked_out",
    ]

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        queryset = self.model.objects.all()
        queryset = queryset.exclude(username="backone")

        return queryset


class AccessSnippetGroup(SnippetViewSetGroup):
    items = (AccessAttemptSVS, AccessFailureLogSVS, AccessLogSVS)
    menu_label = _("Access")
    menu_icon = "lock"


register_snippet(AccessSnippetGroup)
