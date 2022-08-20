from wagtail.contrib.modeladmin.options import (
    ModelAdmin, modeladmin_register, PermissionHelper)
from .models import Members, MemberPeers
from crum import get_current_user
from wagtail.admin.panels import FieldPanel, MultiFieldPanel, FieldRowPanel, ObjectList
from django.utils.translation import gettext as _
from django.forms import HiddenInput


class MemberPeersPermissionHelper(PermissionHelper):
    def user_can_list(self, user):
        return True

    def user_can_create(self, user):
        return False

    def user_can_delete_obj(self, user, obj):
        return False

    def user_can_edit_obj(self, user, obj):
        return False


class MembersAdmin(ModelAdmin):
    model = Members
    inspect_view_enabled = True
    menu_label = 'Members'  # ditch this to use verbose_name_plural from model
    menu_icon = 'list-ul'  # change as required
    add_to_settings_menu = False  # or True to add your model to the Settings sub-menu
    exclude_from_explorer = False # or True to exclude pages of this type from Wagtail's explorer view
    list_display = ('name', 'member_id', 'is_authorized', 'list_ipaddress', 'network',
                    'member_status', 'list_peers')
    list_filter = ('network',)
    search_fields = ('name', 'member_id', 'ipaddress')
    #ordering = ['name']

    def get_edit_handler(self, instance, request):
        basic_panels = [
            MultiFieldPanel([FieldPanel('name'), FieldPanel('description')],
                            heading=_('Network Name and Description')),
            MultiFieldPanel([FieldPanel('member_id', widget=HiddenInput()),
                             FieldPanel('network')],
                            heading=_('Member ID and Network')),
            # MultiFieldPanel([FieldPanel('is_authorized'), FieldPanel('ipaddress')],
            #                heading=_('Authorization and IP Address')),
        ]

        bridge_panels = MultiFieldPanel([FieldRowPanel([FieldPanel('is_bridge'), FieldPanel('is_no_auto_ip')])],
                                        heading=_('Bridge Features'))
        authorize_panels = MultiFieldPanel([FieldPanel('is_authorized'), FieldPanel('ipaddress')],
                                           heading=_('Authorization and IP Address'))
        ipaddress_panels = FieldPanel('ipaddress')

        tags_panels = MultiFieldPanel([FieldPanel('tags')], heading=_('Tagging Features'))

        current_user = get_current_user()
        #print('Handler', current_user)
        custom_panels = basic_panels
        if current_user.is_superuser:
            custom_panels.append(authorize_panels)
            custom_panels.append(bridge_panels)
            custom_panels.append(tags_panels)
        else:
            if current_user.organization.features.authorize:
                custom_panels.append(authorize_panels)
            else:
                custom_panels.append(ipaddress_panels)
            if current_user.organization.features.bridge:
                custom_panels.append(bridge_panels)
            if current_user.organization.features.tags:
                custom_panels.append(tags_panels)

        return ObjectList(custom_panels)

    def get_queryset(self, request):
        #current_user = get_user()
        current_user = get_current_user()
        if not current_user.is_superuser:
            if current_user.organization.is_no_org:
                return Members.objects.filter(user=current_user)
            else:
                return Members.objects.filter(organization=current_user.organization)
        else:
            return Members.objects.all()


class MemberPeersAdmin(ModelAdmin):
    model = MemberPeers
    #inspect_view_enabled = True
    menu_label = 'MemberPeers'  # ditch this to use verbose_name_plural from model
    menu_icon = 'grip'  # change as required
    add_to_settings_menu = False  # or True to add your model to the Settings sub-menu
    exclude_from_explorer = False # or True to exclude pages of this type from Wagtail's explorer view
    list_display = ('member_id', 'network', 'peers', 'updated_at')
    permission_helper_class = MemberPeersPermissionHelper
    list_filter = ('network',)
    #search_fields = ('name', 'member_id', 'ipaddress')
    #ordering = ['name']


modeladmin_register(MembersAdmin)
modeladmin_register(MemberPeersAdmin)