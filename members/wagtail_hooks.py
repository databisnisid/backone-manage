from wagtail.contrib.modeladmin.options import (
    ModelAdmin, ModelAdminGroup, PermissionHelper, modeladmin_register)
from .models import Members
from crum import get_current_user
from wagtail.admin.panels import FieldPanel, MultiFieldPanel
from wagtail.admin.edit_handlers import ObjectList
from django.utils.translation import gettext as _
from controllers.workers import zt_synchronize_member_peers


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

    panels = [
        MultiFieldPanel([FieldPanel('name'), FieldPanel('description')],
                        heading=_('Network Name and Description')),
        MultiFieldPanel([FieldPanel('member_id'),
                         FieldPanel('network')],
                        heading=_('Member ID and Network')),
        MultiFieldPanel([FieldPanel('is_authorized'), FieldPanel('ipaddress')],
                        heading=_('Authorization and IP Address')),
        FieldPanel('is_bridge'),
    ]

    def get_queryset(self, request):
        if not request.user.is_superuser:
            return Members.objects.filter(user=get_current_user())
        else:
            return Members.objects.all()


modeladmin_register(MembersAdmin)