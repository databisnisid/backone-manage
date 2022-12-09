from wagtail.contrib.modeladmin.options import (
    ModelAdmin, PermissionHelper, modeladmin_register)
from wagtail.admin.panels import FieldPanel, MultiFieldPanel
from .models import Controllers
from wagtail.contrib.modeladmin.helpers import ButtonHelper
from django.utils.translation import gettext as _
from controllers.workers import zt_import_all_controllers


class ControllersPermissionHelper(PermissionHelper):
    def user_can_list(self, user):
        return True

    def user_can_create(self, user):
        if user.is_superuser:
            return True
        else:
            return False

    def user_can_delete_obj(self, user, obj):
        if obj.id == 1:
            return False
        else:
            return True

    def user_can_edit_obj(self, user, obj):
        if user.is_superuser:
            return True
        else:
            return False


class ControllerButtonHelper(ButtonHelper):

    # Define classes for our button, here we can set an icon for example
    #import_button_classnames = ["button-small", "icon", "icon-site"]
    synchronize_classnames = ['button button-small button-primary']

    def synchronize_button(self, obj):
        zt_import_all_controllers()
        # Define a label for our button
        text = _('Synchronize')
        return {
            'url': self.url_helper.index_url, # Modify this to get correct action
            'label': text,
            'classname': self.finalise_classname(self.synchronize_classnames),
            'title': text,
        }

    def get_buttons_for_obj(
        self, obj, exclude=None, classnames_add=None, classnames_exclude=None
    ):
        """
        This function is used to gather all available buttons.
        We append our custom button to the btns list.
        """
        buttons = super().get_buttons_for_obj(
            obj, exclude, classnames_add, classnames_exclude
        )
        if 'synchronize_button' not in (exclude or []):
            buttons.append(self.synchronize_button(obj))
        return buttons


class ControllersAdmin(ModelAdmin):
    model = Controllers
    #button_helper_class = ControllerButtonHelper   # Uncomment this to enable button
    #inspect_view_enabled = True
    menu_label = 'Controllers'  # ditch this to use verbose_name_plural from model
    menu_icon = 'user'  # change as required
    add_to_settings_menu = False  # or True to add your model to the Settings sub-menu
    exclude_from_explorer = False # or True to exclude pages of this type from Wagtail's explorer view
    list_display = ('name', 'uri', 'node_id', 'version', 'status')
    search_fields = ('name', 'node_id')
    list_filter = ('controller',)
    permission_helper_class = ControllersPermissionHelper

    panels = [
        MultiFieldPanel([FieldPanel('name'), FieldPanel('description')],
                        heading=_('Controller Name and Description')),
        MultiFieldPanel([FieldPanel('uri'), FieldPanel('token')],
                        heading=_('Network URL and Token')),
    ]

    def __init__(self, *args, **kwargs):
        #request = kwargs.get('request')
        #print('User ', self.current_user)
        self.inspect_view_enabled = True
        super().__init__(*args, **kwargs)


# Now you just need to register your customised ModelAdmin class with Wagtail
modeladmin_register(ControllersAdmin)
