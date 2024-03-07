from wagtail.contrib.modeladmin.options import (
    ModelAdmin, ModelAdminGroup, PermissionHelper, modeladmin_register)
from wagtail.admin.panels import FieldPanel, MultiFieldPanel, FieldRowPanel
from django.utils.translation import gettext_lazy as _
from .models import Licenses
from accounts.models import Organizations


class LicensesPermissionHelper(PermissionHelper):
    '''

    def user_can_list(self, user):
        return True
    '''
    
    def user_can_create(self, user):
        if user.is_superuser:
            if Licenses.objects.all().count() < Organizations.objects.all().count():
                return True
            else:
                return False
        else:
            return False

    def user_can_delete_obj(self, user, obj):
        return False

    '''
    def user_can_edit_obj(self, user, obj):
        return False
    '''


class LicensesAdmin(ModelAdmin):
    model = Licenses
    #button_helper_class = ControllerButtonHelper   # Uncomment this to enable button
    inspect_view_enabled = True
    menu_label = 'License'  # ditch this to use verbose_name_plural from model
    menu_icon = 'key'  # change as required
    add_to_settings_menu = True  # or True to add your model to the Settings sub-menu
    exclude_from_explorer = False # or True to exclude pages of this type from Wagtail's explorer view
    list_display = ('node_id', 'get_organization_uuid', 'organization', 'get_license_time',)
    #search_fields = ('node_id', )
    permission_helper_class = LicensesPermissionHelper

    panels = [
        FieldPanel('node_id', read_only=True),
        FieldPanel('organization'),
        MultiFieldPanel([
            FieldPanel('license_key'),
            FieldPanel('license_string'),
            ], heading=_('License'))
    ]

    '''
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
    '''

modeladmin_register(LicensesAdmin)

