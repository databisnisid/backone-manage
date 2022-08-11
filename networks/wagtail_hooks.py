from wagtail.contrib.modeladmin.options import (
    ModelAdmin, ModelAdminGroup, PermissionHelper, modeladmin_register)
from .models import Networks, NetworkRoutes, NetworkRules, Members
from crum import get_current_user
from wagtail.admin.panels import FieldPanel, MultiFieldPanel
from wagtail.admin.edit_handlers import ObjectList
from django.utils.translation import gettext as _
from controllers.workers import zt_synchronize_member_peers

class NetworkRoutesPermissionHelper(PermissionHelper):
    '''

    def user_can_list(self, user):
        return True

    def user_can_create(self, user):
        if user.is_superuser:
            return True
        else:
            return False
    '''

    def user_can_delete_obj(self, user, obj):
        if obj.gateway is None:
            return False
        else:
            return True

    def user_can_edit_obj(self, user, obj):
        return False


class NetworksAdmin(ModelAdmin):
    model = Networks
    inspect_view_enabled = True
    menu_label = 'Networks'  # ditch this to use verbose_name_plural from model
    menu_icon = 'site'  # change as required
    add_to_settings_menu = False  # or True to add your model to the Settings sub-menu
    exclude_from_explorer = False # or True to exclude pages of this type from Wagtail's explorer view
    list_display = ('name', 'network_id', 'ip_allocation')
    #list_filter = ('name',)
    search_fields = ('name',)

    panels = [
        MultiFieldPanel([FieldPanel('name'), FieldPanel('description')],
                        heading=_('Network Name and Description')),
        MultiFieldPanel([FieldPanel('ip_assignment'), FieldPanel('ip_assignment_netmask')],
                        heading=_('IP Assignment')),
        FieldPanel('user', classname=None, widget=None, heading='',
                   disable_comments=False, permission='superuser')
    ]

    #def __init__(self, *args, **kwargs):
    #    super().__init__(*args, **kwargs)

    '''
    def get_edit_handler(self, instance, request):
        panels = self.panels
        if request.user.is_superuser:
            panels = self.panels_admin

        return ObjectList(panels)
    '''

    def get_queryset(self, request):
        if not request.user.is_superuser:
            return Networks.objects.filter(user=get_current_user())
        else:
            return Networks.objects.all()


class NetworkRoutesAdmin(ModelAdmin):
    model = NetworkRoutes
    #inspect_view_enabled = True
    menu_label = 'Network Routes'  # ditch this to use verbose_name_plural from model
    menu_icon = 'redirect'  # change as required
    add_to_settings_menu = False  # or True to add your model to the Settings sub-menu
    exclude_from_explorer = False # or True to exclude pages of this type from Wagtail's explorer view
    list_display = ('__str__', 'gateway', 'network',)
    list_filter = ('network',)
    search_fields = ('__str__',)
    ordering = ['network', 'gateway']
    permission_helper_class = NetworkRoutesPermissionHelper
    #base_form_class = NetworkRoutesForm

    panels = [
        MultiFieldPanel([FieldPanel('ip_network'), FieldPanel('ip_netmask'), FieldPanel('gateway')],
                        heading=_('Target and Gateway')),
        FieldPanel('network'),
    ]

    def get_queryset(self, request):
        if not request.user.is_superuser:
            return NetworkRoutes.objects.filter(user=get_current_user())
        else:
            return NetworkRoutes.objects.all()


class NetworkRulesAdmin(ModelAdmin):
    model = NetworkRules
    #inspect_view_enabled = True
    menu_label = 'Network Rules'  # ditch this to use verbose_name_plural from model
    menu_icon = 'tag'  # change as required
    add_to_settings_menu = False  # or True to add your model to the Settings sub-menu
    exclude_from_explorer = False # or True to exclude pages of this type from Wagtail's explorer view
    list_display = ('network',)
    #list_filter = ('network',)
    #search_fields = ('__str__',)
    #ordering = ['network', 'gateway']
    #permission_helper_class = NetworkRoutesPermissionHelper
    panels = [
        MultiFieldPanel([FieldPanel('network'),
                         FieldPanel('rules')],
                        heading=_('Network Rules')),
    ]

    def get_queryset(self, request):
        if not request.user.is_superuser:
            return NetworkRules.objects.filter(user=get_current_user())
        else:
            return NetworkRules.objects.all()


class MembersAdmin(ModelAdmin):
    model = Members
    inspect_view_enabled = True
    menu_label = 'Members'  # ditch this to use verbose_name_plural from model
    menu_icon = 'list-ul'  # change as required
    add_to_settings_menu = False  # or True to add your model to the Settings sub-menu
    exclude_from_explorer = False # or True to exclude pages of this type from Wagtail's explorer view
    list_display = ('name', 'member_id', 'is_authorized', 'ipaddress', 'network',
                    'member_status', 'list_peers')
    list_filter = ('network',)
    search_fields = ('name', 'member_id', 'ipaddress')
    #ordering = ['name']

    panels = [
        MultiFieldPanel([FieldPanel('name'), FieldPanel('description')],
                        heading=_('Network Name and Description')),
        MultiFieldPanel([FieldPanel('member_id'),
                         FieldPanel('network')],
                        heading=_('Member ID and Network')),
        MultiFieldPanel([FieldPanel('is_authorized'), FieldPanel('ipaddress')],
                        heading=_('Authorization and IP Address')),
    ]

    def get_queryset(self, request):
        zt_synchronize_member_peers()

        if not request.user.is_superuser:
            return Members.objects.filter(user=get_current_user())
        else:
            return Members.objects.all()


class NetworksGroup(ModelAdminGroup):
    menu_label = 'Networks'
    menu_icon = 'folder-open-inverse'  # change as required
    menu_order = 300  # will put in 3rd place (000 being 1st, 100 2nd)
    items = (NetworksAdmin, NetworkRoutesAdmin, NetworkRulesAdmin, MembersAdmin)


# Now you just need to register your customised ModelAdmin class with Wagtail
modeladmin_register(NetworksAdmin)
modeladmin_register(NetworkRoutesAdmin)
#modeladmin_register(NetworkRulesAdmin)
modeladmin_register(MembersAdmin)
