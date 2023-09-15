from wagtail.contrib.modeladmin.options import (
    ModelAdmin, ModelAdminGroup, PermissionHelper, modeladmin_register)
from wagtail.admin.panels import FieldPanel, MultiFieldPanel, FieldRowPanel
from .models import Features
from django.utils.translation import gettext_lazy as _
from .models import Organizations


class AccountsPermissionHelper(PermissionHelper):
    '''

    def user_can_list(self, user):
        return True

    def user_can_create(self, user):
        if user.is_superuser:
            return True
        else:
            return False
    '''

    def user_can_delete_obj(self, user, obj):
        if obj.id == 1:
            return False
        else:
            return True
    '''
    def user_can_edit_obj(self, user, obj):
        return False
    '''


class OrganizationsAdmin(ModelAdmin):
    model = Organizations
    #button_helper_class = ControllerButtonHelper   # Uncomment this to enable button
    #inspect_view_enabled = True
    menu_label = 'Organizations'  # ditch this to use verbose_name_plural from model
    menu_icon = 'group'  # change as required
    add_to_settings_menu = True  # or True to add your model to the Settings sub-menu
    exclude_from_explorer = False # or True to exclude pages of this type from Wagtail's explorer view
    list_display = ('name', 'features')
    search_fields = ('name', 'features')
    permission_helper_class = AccountsPermissionHelper

    panels = [
        MultiFieldPanel([FieldPanel('name'), FieldPanel('features')],
                        heading=_('Name and Features')),
        FieldPanel('controller'),
        FieldPanel('is_no_org'),
    ]

    def __init__(self, *args, **kwargs):
        #request = kwargs.get('request')
        #print('User ', self.current_user)
        #self.inspect_view_enabled = True
        super().__init__(*args, **kwargs)


class FeaturesAdmin(ModelAdmin):
    model = Features
    menu_label = 'Features'  # ditch this to use verbose_name_plural from model
    menu_icon = 'snippet'  # change as required
    add_to_settings_menu = True  # or True to add your model to the Settings sub-menu
    exclude_from_explorer = False # or True to exclude pages of this type from Wagtail's explorer view
    list_display = ('name', 'description')
    list_filter = ('name',)
    search_fields = ('name',)
    #ordering = ['name']
    permission_helper_class = AccountsPermissionHelper

    panels = [
        MultiFieldPanel([FieldPanel('name'), FieldPanel('description')],
                        heading=_('Name and Description')),
        MultiFieldPanel([
            FieldRowPanel([
                FieldPanel('network_multi_ip'),
                FieldPanel('network_rules')], classname="collapsible collapsed"),
            FieldPanel('number_of_network')],
            heading=_('Network Features')),
        MultiFieldPanel([
            FieldRowPanel([FieldPanel('authorize'), FieldPanel('member_multi_ip')]),
            FieldRowPanel([FieldPanel('bridge'), FieldPanel('tags')])],
            #FieldRowPanel([FieldPanel('synchronize')])],
            heading=_('Member Features')),
        MultiFieldPanel([
            FieldRowPanel([FieldPanel('web'), FieldPanel('ssh')])],
            heading=_('Remote Access Features')),
        MultiFieldPanel([
            FieldRowPanel([FieldPanel('geolocation'), FieldPanel('online_offline')]),
            FieldRowPanel([FieldPanel('is_export'), FieldPanel('mobile_connect')]),
            FieldRowPanel([FieldPanel('map_dashboard'), FieldPanel('is_nms')])],
            heading=_('Additional Features')),
        MultiFieldPanel([
            FieldRowPanel([FieldPanel('is_telkomsel')])],
            heading=_('Project Related'))
    ]


class AccountsGroup(ModelAdminGroup):
    menu_label = 'Accounts'
    menu_icon = 'folder-open-inverse'  # change as required
    menu_order = 200  # will put in 3rd place (000 being 1st, 100 2nd)
    items = (OrganizationsAdmin, FeaturesAdmin)


# Now you just need to register your customised ModelAdmin class with Wagtail
#modeladmin_register(AccountsGroup)
modeladmin_register(FeaturesAdmin)
modeladmin_register(OrganizationsAdmin)
