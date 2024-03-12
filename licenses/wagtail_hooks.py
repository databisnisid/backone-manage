from wagtail.contrib.modeladmin.options import (
    ModelAdmin, ModelAdminGroup, ObjectList, PermissionHelper, modeladmin_register)
from wagtail.admin.panels import FieldPanel, MultiFieldPanel, FieldRowPanel
from django.utils.translation import gettext_lazy as _
from .models import Licenses
from accounts.models import Organizations
from crum import get_current_user


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
        if user.is_superuser:
            return True
        else:
            return False

    '''
    def user_can_edit_obj(self, user, obj):
        return False
    '''


class LicensesAdmin(ModelAdmin):
    model = Licenses
    #button_helper_class = ControllerButtonHelper   # Uncomment this to enable button
    #inspect_view_enabled = True
    menu_label = 'License'  # ditch this to use verbose_name_plural from model
    menu_icon = 'key'  # change as required
    add_to_settings_menu = True  # or True to add your model to the Settings sub-menu
    exclude_from_explorer = False # or True to exclude pages of this type from Wagtail's explorer view
    list_display = ('node_id', 'get_organization_uuid', 'get_controller_token', 'organization', 'get_license_time', 'get_license_msg',)
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

    def get_edit_handler(self):
        superuser_panels = [
            FieldPanel('node_id', read_only=True),
            FieldPanel('organization'),
            MultiFieldPanel([
                FieldPanel('license_key'),
                FieldPanel('license_string'),
                ], heading=_('License'))
        ]

        admin_panels = [
            FieldPanel('node_id', read_only=True),
            FieldPanel('organization', read_only=True),
            MultiFieldPanel([
                FieldPanel('license_string'),
                ], heading=_('License'))
        ]

        current_user = get_current_user()
        if current_user.is_superuser:
            return ObjectList(superuser_panels)
        else:
            return ObjectList(admin_panels)


    ''' Working INIT modeladmin '''
    ''' Not Really Working. Need more test '''
    '''
    def __init__(self, *args, **kwargs):
        self.inspect_view_enabled = False
        super(LicensesAdmin, self).__init__(*args, **kwargs)
    '''

modeladmin_register(LicensesAdmin)

