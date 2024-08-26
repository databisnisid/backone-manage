from wagtail.contrib.modeladmin.options import (
    ModelAdmin, ModelAdminGroup, PermissionHelper, modeladmin_register)
from wagtail.admin.panels import FieldPanel, MultiFieldPanel, FieldRowPanel
from .models import ZabbixNetworks
from django.utils.translation import gettext_lazy as _


class ZabbixNetworksAdmin(ModelAdmin):
    model = ZabbixNetworks
    menu_label = 'Zabbix Networks'  # ditch this to use verbose_name_plural from model
    menu_icon = 'group'  # change as required
    add_to_settings_menu = True  # or True to add your model to the Settings sub-menu
    exclude_from_explorer = False # or True to exclude pages of this type from Wagtail's explorer view
    list_display = ('name')

    panels = [
        FieldPanel('name'),
        FieldPanel('networks'),
    ]

modeladmin_register(ZabbixNetworksAdmin)

