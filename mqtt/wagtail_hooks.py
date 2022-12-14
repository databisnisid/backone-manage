from wagtail.contrib.modeladmin.options import (
    ModelAdmin, PermissionHelper, modeladmin_register)
from .models import Mqtt
from wagtail.admin.panels import FieldPanel, MultiFieldPanel, ObjectList
from django.utils.translation import gettext as _
from crum import get_current_user


class MqttAdmin(ModelAdmin):
    model = Mqtt
    inspect_view_enabled = True
    menu_label = 'MQTT'  # ditch this to use verbose_name_plural from model
    menu_icon = 'doc-full'  # change as required
    add_to_settings_menu = False  # or True to add your model to the Settings sub-menu
    exclude_from_explorer = False # or True to exclude pages of this type from Wagtail's explorer view
    list_display = ('member_id', 'model', 'board_name',
                    'release_version', 'release_target', 'updated_at', 'ipaddress')
    search_fields = ('member_id',)


modeladmin_register(MqttAdmin)

