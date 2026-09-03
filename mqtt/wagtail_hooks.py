from wagtail import hooks
from wagtail.snippets.models import register_snippet
from wagtail.snippets.views.snippets import SnippetViewSet
from .models import Mqtt
from wagtail.admin.panels import FieldPanel, MultiFieldPanel, ObjectList
from django.utils.translation import gettext as _
from crum import get_current_user




@hooks.register("construct_snippet_listing_buttons")
def remove_snippet_edit_button_mqtt(buttons, snippet, user, context=None):
    for button in buttons:
        index = buttons.index(button)

        if "edit" in button.label.lower():
            if "mqtt/mqtt/" in button.url:
                buttons.pop(index)
                break


# class MqttAdmin(ModelAdmin):
class MqttAdmin(SnippetViewSet):
    model = Mqtt
    inspect_view_enabled = True
    # index_template_name = 'mqtt/snippets/index.html'
    menu_label = "MQTT"  # ditch this to use verbose_name_plural from model
    # add_to_settings_menu = False  # or True to add your model to the Settings sub-menu
    exclude_from_explorer = (
        False  # or True to exclude pages of this type from Wagtail's explorer view
    )
    list_display = ("member_id", "message", "updated_at")
    search_fields = ("member_id",)

    # Wagtail 5.1.1
    add_to_admin_menu = True
    menu_order = 999
    list_per_page = 50
    icon = "doc-full"  # change as required
    # menu_icon = 'doc-full'  # change as required


"""
class MqttRedisAdmin(SnippetViewSet):
    model = MqttRedis
    inspect_view_enabled = True
    menu_label = "MQTT Redis"  # ditch this to use verbose_name_plural from model
    exclude_from_explorer = (
        False  # or True to exclude pages of this type from Wagtail's explorer view
    )
    list_display = ("member_id", "message", "updated_at")
    search_fields = ("member_id",)
    add_to_admin_menu = True
    menu_order = 999
    list_per_page = 50
    icon = "doc-full"  # change as required

"""

# modeladmin_register(MqttAdmin)
register_snippet(MqttAdmin)
# register_snippet(MqttRedisAdmin)
