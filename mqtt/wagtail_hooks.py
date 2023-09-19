#from wagtail.contrib.modeladmin.options import (
#    ModelAdmin, PermissionHelper, modeladmin_register)
from wagtail.snippets.models import register_snippet
from wagtail.snippets.views.snippets import SnippetViewSet
from .models import Mqtt
from wagtail.admin.panels import FieldPanel, MultiFieldPanel, ObjectList
from django.utils.translation import gettext as _
from crum import get_current_user

from wagtail import hooks
from wagtail.users.widgets import UserListingButton
from wagtail.snippets import widgets as wagtailsnippets_widgets


'''
@hooks.register('register_snippet_listing_buttons')
def snippet_listing_buttons(snippet, user, next_url=None):
    yield wagtailsnippets_widgets.SnippetListingButton(
        'Button 1 Check Me',
        '/goes/to/a/url/',
        priority=11
    )
    yield wagtailsnippets_widgets.SnippetListingButton(
        'Button 2 Check Me',
        '/goes/to/a/url/',
        priority=11
    )


@hooks.register('construct_snippet_listing_buttons')
def remove_snippet_edit_button_item(buttons, snippet, user, context=None):
    for button in buttons:
        index = buttons.index(button)

        if 'edit' in button.label.lower():
            buttons.pop(index)
            break


@hooks.register('construct_snippet_listing_buttons')
def remove_snippet_delete_button_item(buttons, snippet, user, context=None):
    for button in buttons:
        index = buttons.index(button)

        if 'delete' in button.label.lower():
            buttons.pop(index)
            break
'''

@hooks.register('construct_snippet_listing_buttons')
def remove_snippet_edit_button_mqtt(buttons, snippet, user, context=None):
    for button in buttons:
        index = buttons.index(button)

        if 'edit' in button.label.lower():
            if 'mqtt/mqtt/' in button.url:
                buttons.pop(index)
                break

#class MqttAdmin(ModelAdmin):
class MqttAdmin(SnippetViewSet):
    model = Mqtt
    inspect_view_enabled = True
    index_template_name = 'mqtt/snippets/index.html'
    menu_label = 'MQTT'  # ditch this to use verbose_name_plural from model
    #add_to_settings_menu = False  # or True to add your model to the Settings sub-menu
    exclude_from_explorer = False # or True to exclude pages of this type from Wagtail's explorer view
    list_display = ('member_id', 'model', 'board_name',
                    'release_version', 'release_target', 'updated_at', 'ipaddress')
    search_fields = ('member_id',)

    # Wagtail 5.1.1
    add_to_admin_menu = True
    menu_order = 999
    list_per_page = 50
    icon = 'doc-full'  # change as required


#modeladmin_register(MqttAdmin)
register_snippet(MqttAdmin)

