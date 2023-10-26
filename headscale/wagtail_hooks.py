from requests import request
from wagtail.contrib.modeladmin.options import (
    ModelAdmin, ModelAdminGroup, modeladmin_register, ButtonHelper, PermissionHelper)
from wagtail.snippets.models import register_snippet
from wagtail.snippets.views.snippets import SnippetViewSet
from wagtail.contrib.modeladmin.views import ModelFormView, InstanceSpecificView
from .models import HS_Users, HS_Preauthkeys, HS_Nodes
from crum import get_current_user
from wagtail.admin.panels import FieldPanel, InlinePanel, MultiFieldPanel, FieldRowPanel, ObjectList
from wagtailgeowidget import geocoders
from wagtailgeowidget.panels import GeoAddressPanel, GoogleMapsPanel
from django.utils.translation import gettext as _
from django.utils import timezone


class HS_PreauthkeysPermission(PermissionHelper):
    def user_can_list(self, user):
        return True

    def user_can_create(self, user):
        return True

    def user_can_delete_obj(self, user, obj):
        return False

    def user_can_edit_obj(self, user, obj):
        return False


class HS_NodesPermission(PermissionHelper):
    def user_can_list(self, user):
        return True

    def user_can_create(self, user):
        return False

    def user_can_delete_obj(self, user, obj):
        return False

    def user_can_edit_obj(self, user, obj):
        return True


class HS_UsersAdmin(ModelAdmin):
    model = HS_Users
    menu_label = 'Network'
    menu_icon = 'link'
    add_to_settings_menu = False
    list_display = ['name', 'description', 'created_at']
    search_fields = ['name']

    panels = [
            MultiFieldPanel([
                FieldPanel('name'),
                FieldPanel('description'),
                ], heading=_('Name and Description'))
            ]

    def get_queryset(self, request):

        if request.user.is_superuser:
            return HS_Users.objects.all()
        else:
            return None


class HS_PreauthkeysAdmin(ModelAdmin):
    model = HS_Preauthkeys
    menu_label = 'Auth Keys'
    menu_icon = 'key'
    add_to_settings_menu = False
    list_display = ['key', 'is_reusable', 'is_ephemeral', 'is_used', 'expiration']
    list_filter = ['hs_user']
    permission_helper_class = HS_PreauthkeysPermission

    panels = [
            MultiFieldPanel([
                FieldPanel('hs_user'),
                FieldRowPanel([
                    FieldPanel('is_reusable'),
                    FieldPanel('is_ephemeral'),
                    ])
                ], heading=_('Network and Options')),
            ]

    def get_queryset(self, request):
        current_time = timezone.now()
        if request.user.is_superuser:
            return HS_Preauthkeys.objects.filter(expiration__gt=current_time)
            #return HS_Preauthkeys.objects.all()
        else:
            return HS_Preauthkeys.objects.filter(organization=request.user.organization, expiration__gt=current_time)
            #return HS_Preauthkeys.objects.filter(organization=request.user.organization)

    def get_list_display(self, request):
        list_display = ['key', 'is_reusable', 'is_ephemeral', 'is_used']
        if request.user.is_superuser:
            list_display = ['hs_user', 'key', 'is_reusable', 'is_ephemeral', 'is_used', 'expiration']

        return list_display


class HS_NodesAdmin(ModelAdmin):
    model = HS_Nodes
    menu_label = 'Nodes'
    menu_icon = 'site'
    inspect_view_enabled = True
    add_to_settings_menu = False
    permission_helper_class = HS_NodesPermission
    list_display = ('name', 'ipaddress_v4', 'hostname', 'given_name')
    list_filter = ['hs_user']
    search_fields = ['name', 'ipaddress_v4']


    '''
    panels = [
            MultiFieldPanel([
                FieldPanel('name'),
                FieldPanel('description'),
                ], heading=_('Name and Description')),
            MultiFieldPanel([
                FieldPanel('ipaddress_v4', read_only=True),
                FieldPanel('ipaddress_v6', read_only=True),
                FieldPanel('hostname', read_only=True),
                FieldPanel('given_name', read_only=True),
                ], heading=_('Parameters')),
            ]
    '''

    def get_edit_handler(self):
        basic_panels = [
                MultiFieldPanel([
                    FieldPanel('name'),
                    FieldPanel('description'),
                    ], heading=_('Name and Description')),
                MultiFieldPanel([
                    FieldPanel('ipaddress_v4', read_only=True),
                    FieldPanel('ipaddress_v6', read_only=True),
                    FieldPanel('hostname', read_only=True),
                    FieldPanel('given_name', read_only=True),
                    ], heading=_('Parameters'), classname="collapsed"),
                ]

        mobile_connect_panels = MultiFieldPanel([
            FieldRowPanel([
                FieldPanel('mobile_number_first')
                ])
            ], heading=_('Mobile Connection'), classname="collapsed")

        geolocation_panels = MultiFieldPanel([
                GeoAddressPanel("address", geocoder=geocoders.GOOGLE_MAPS),
                GoogleMapsPanel('location', address_field='address'),
            ], heading=_('Geo Location'), classname="collapsed")

        connection_panels = MultiFieldPanel([
                FieldRowPanel([
                    FieldPanel('online_at'),
                    FieldPanel('offline_at')
                    ])
            ], heading=_('Online/Offline'), classname="collapsed")

        custom_panels = basic_panels

        current_user = get_current_user()

        if current_user.is_superuser:
            custom_panels.append(mobile_connect_panels)
            custom_panels.append(geolocation_panels)
            custom_panels.append(connection_panels)
        else:
            if current_user.organization.features.online_offline:
                custom_panels.append(connection_panels)
            if current_user.organization.features.geolocation:
                custom_panels.append(geolocation_panels)
            if current_user.organization.features.mobile_connect:
                custom_panels.append(mobile_connect_panels)

        return ObjectList(custom_panels)


    def get_queryset(self, request):
        if request.user.is_superuser:
            return HS_Nodes.objects.all()
        else:
            return HS_Nodes.objects.filter(organization=request.user.organization)

    def get_list_display(self, request):
        list_display = ('node_name_with_address', 'node_status')
        #list_display = ('name', 'ipaddress_v4', 'is_online')
        if request.user.is_superuser:
            list_display = ('node_name_with_address', 'node_status', 'last_seen')

        return list_display


class HSAdminGroup(ModelAdminGroup):
    menu_label = _('Backone HS')
    menu_icon = 'pick'
    items = (HS_UsersAdmin, HS_PreauthkeysAdmin, HS_NodesAdmin)


modeladmin_register(HSAdminGroup)


