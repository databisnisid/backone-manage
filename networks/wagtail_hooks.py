from wagtail.contrib.modeladmin.options import (
    ModelAdmin, PermissionHelper, modeladmin_register)
from .models import Networks, NetworkRoutes, NetworkRules
from config.utils import get_user
from wagtail.admin.panels import FieldPanel, MultiFieldPanel, ObjectList
from django.utils.translation import gettext as _
from crum import get_current_user
from wagtail.admin.forms import WagtailAdminPageForm
from wagtail import hooks
from django.core.exceptions import ObjectDoesNotExist


'''
@hooks.register('construct_homepage_panels', order=1)
def add_user_org_panel(request, panels):
    user_org_panels = MultiFieldPanel([FieldPanel('user'), FieldPanel('organization')],
                                      heading=_('User and Organization'))
    if request.user.is_superuser:
        print(panels)
        panels.append(user_org_panels)
'''

class NetworkRulesPermissionHelper(PermissionHelper):
    def user_can_list(self, user):
        return True

    def user_can_create(self, user):
        return False

    def user_can_delete_obj(self, instance, obj):
        return False

    def user_can_edit_obj(self, instance, obj):
        return True


class NetworkRoutesPermissionHelper(PermissionHelper):
    def user_can_list(self, user):
        return True

    def user_can_create(self, user):
        return True

    def user_can_delete_obj(self, instance, obj):
        print('Instance Delete', instance)
        if obj.gateway is None:
            return False
        else:
            return True

    def user_can_edit_obj(self, instance, obj):
        return False

'''
class RestrictedFieldPanel(FieldPanel):
    def required_fields(self):
        current_user = get_current_user()
        #if self.request and self.request.user.is_superuser:
        print('FieldPanels', current_user)
        if current_user.is_superuser:
            return super().required_fields()
        return []
'''


class NetworksAdmin(ModelAdmin):
    model = Networks
    inspect_view_enabled = True
    menu_label = 'Networks'  # ditch this to use verbose_name_plural from model
    menu_icon = 'link'  # change as required
    add_to_settings_menu = False  # or True to add your model to the Settings sub-menu
    exclude_from_explorer = False # or True to exclude pages of this type from Wagtail's explorer view
    list_display = ('name', 'network_id', 'ip_allocation')
    #list_filter = ('name',)
    search_fields = ('name',)
    #base_form_class = NetworksForm

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        #try:
        #    user = kwargs['user']
        #except (AttributeError, KeyError):
        #    pass
        #else:
        #    if self.user is None:
        #        self.user = get_current_user()

    def get_edit_handler(self, instance, request):
        basic_panels = [
            MultiFieldPanel([FieldPanel('name'), FieldPanel('description')],
                            heading=_('Network Name and Description')),
            MultiFieldPanel([FieldPanel('ip_address_networks')],
                            heading=_('IP Network')),
        ]
        superuser_panels = [
            MultiFieldPanel([FieldPanel('name'), FieldPanel('description')],
                            heading=_('Network Name and Description')),
            MultiFieldPanel([FieldPanel('ip_address_networks')],
                            heading=_('IP Network')),
            MultiFieldPanel([FieldPanel('user')],
                            heading=_('Network Owner'))
        ]

        current_user = get_current_user()

        if current_user.is_superuser:
            custom_panels = superuser_panels
        else:
            custom_panels = basic_panels

        return ObjectList(custom_panels)

    def get_queryset(self, request):
        current_user = get_current_user()
        print('Query Set', current_user, current_user.organization.is_no_org)
        if not current_user.is_superuser:
            if current_user.organization.is_no_org:
                print('No Orgs')
                return Networks.objects.filter(user=current_user)
            else:
                return Networks.objects.filter(organization=current_user.organization)
        else:
            return Networks.objects.all()


class NetworkRoutesAdmin(ModelAdmin):
    model = NetworkRoutes
    #inspect_view_enabled = True
    menu_label = 'Network Routes'  # ditch this to use verbose_name_plural from model
    menu_icon = 'redirect'  # change as required
    add_to_settings_menu = False  # or True to add your model to the Settings sub-menu
    exclude_from_explorer = False # or True to exclude pages of this type from Wagtail's explorer view
    list_display = ('ip_network', 'gateway', 'network',)
    list_filter = ('network',)
    search_fields = ('ip_network', 'gateway')
    ordering = ['network', 'gateway']
    permission_helper_class = NetworkRoutesPermissionHelper
    #base_form_class = NetworkRoutesForm

    panels = [
        MultiFieldPanel([FieldPanel('ip_network'), FieldPanel('gateway')],
                        heading=_('Target and Gateway')),
        FieldPanel('network'),
    ]

    def get_queryset(self, request):
        #current_user = get_user()
        current_user = get_current_user()
        if not request.user.is_superuser:
            if current_user.organization.is_no_org:
                return NetworkRoutes.objects.filter(user=current_user)
            else:
                return NetworkRoutes.objects.filter(organization=current_user.organization)
        else:
            return NetworkRoutes.objects.all()


class NetworkRulesAdmin(ModelAdmin):
    model = NetworkRules
    inspect_view_enabled = True
    menu_label = 'Network Rules'  # ditch this to use verbose_name_plural from model
    menu_icon = 'tag'  # change as required
    add_to_settings_menu = False  # or True to add your model to the Settings sub-menu
    exclude_from_explorer = False # or True to exclude pages of this type from Wagtail's explorer view
    list_display = ('name', 'network',)
    list_filter = ('network',)
    #search_fields = ('__str__',)
    #ordering = ['network', 'gateway']
    permission_helper_class = NetworkRulesPermissionHelper

    def get_edit_handler(self, instance=None, request=None):
        basic_panels = [
            MultiFieldPanel([FieldPanel('network'),
                             FieldPanel('rules_definition')],
                            heading=_('Network Rules')),
        ]

        advance_panels = [
            MultiFieldPanel([FieldPanel('network'),
                             FieldPanel('rules_definition'),
                             FieldPanel('rules')],
                            heading=_('Network Rules')),
        ]
        current_user = get_current_user()
        if current_user.is_superuser:
            return ObjectList(advance_panels)
        else:
            return ObjectList(basic_panels)

    def get_queryset(self, request):
        #current_user = get_user()
        current_user = get_current_user()
        if not current_user.is_superuser:
            if current_user.organization.is_no_org:
                return NetworkRules.objects.filter(user=current_user)
            else:
                return NetworkRules.objects.filter(organization=current_user.organization)
        else:
            return NetworkRules.objects.all()


# Now you just need to register your customised ModelAdmin class with Wagtail
modeladmin_register(NetworksAdmin)
modeladmin_register(NetworkRoutesAdmin)
modeladmin_register(NetworkRulesAdmin)

