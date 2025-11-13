# from wagtail.contrib.modeladmin.options import (
from wagtail_modeladmin.options import (
    ModelAdmin,
    ModelAdminGroup,
    PermissionHelper,
    modeladmin_register,
)
from wagtail.admin.panels import FieldPanel, MultiFieldPanel, FieldRowPanel
from .models import ZabbixConfigs, ZabbixNetworks
from django.utils.translation import gettext_lazy as _


class ZabbixNetworksPermissionHelper(PermissionHelper):
    def user_can_create(self, user):
        if ZabbixConfigs.objects.count() > ZabbixNetworks.objects.count():
            return True
        else:
            return False


class ZabbixConfigsAdmin(ModelAdmin):
    model = ZabbixConfigs
    menu_label = "Zabbix Configs"  # ditch this to use verbose_name_plural from model
    menu_icon = "cog"  # change as required
    add_to_settings_menu = True  # or True to add your model to the Settings sub-menu
    exclude_from_explorer = (
        False  # or True to exclude pages of this type from Wagtail's explorer view
    )
    list_display = ["name"]


class ZabbixNetworksAdmin(ModelAdmin):
    model = ZabbixNetworks
    menu_label = "Zabbix Networks"  # ditch this to use verbose_name_plural from model
    menu_icon = "cogs"  # change as required
    add_to_settings_menu = True  # or True to add your model to the Settings sub-menu
    exclude_from_explorer = (
        False  # or True to exclude pages of this type from Wagtail's explorer view
    )
    list_display = ["name"]
    permission_helper_class = ZabbixNetworksPermissionHelper
    form_view_extra_js = ["zabbix/js/disable_name.js"]


modeladmin_register(ZabbixConfigsAdmin)
modeladmin_register(ZabbixNetworksAdmin)
