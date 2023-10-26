from wagtail.contrib.modeladmin.options import (
    ModelAdmin, PermissionHelper, modeladmin_register)
from .models import WebFilters
from wagtail.admin.panels import FieldPanel, InlinePanel, MultiFieldPanel, ObjectList
from django.utils.translation import gettext as _
from crum import get_current_user



class WebfiltersPermissionHelper(PermissionHelper):
    def user_can_list(self, user):
        return True

    def user_can_create(self, user):
        return True

    def user_can_delete_obj(self, user, obj):
        return True

    def user_can_edit_obj(self, user, obj):
        return True


class WebfiltersAdmin(ModelAdmin):
    model = WebFilters
    inspect_view_enabled = True
    menu_label = 'WebFilters'  # ditch this to use verbose_name_plural from model
    menu_icon = 'globe'  # change as required
    add_to_settings_menu = False  # or True to add your model to the Settings sub-menu
    exclude_from_explorer = False # or True to exclude pages of this type from Wagtail's explorer view
    list_display = ('name', 'uuid')
    #list_filter = ('name',)
    search_fields = ('name', 'uuid',)
    #list_filter = ('controller',)
    #base_form_class = NetworksForm
    permission_helper_class = WebfiltersPermissionHelper

    def get_queryset(self, request):
        if not request.user.is_superuser:
            if request.user.organization.is_no_org:
                return WebFilters.objects.filter(user=request.user)
            else:
                return WebFilters.objects.filter(organization=request.user.organization)
        else:
            return WebFilters.objects.all()

    def get_edit_handler(self):
        basic_panels = [
                MultiFieldPanel([
                    FieldPanel('name'),
                    FieldPanel('description'),
                    ], heading=_('Name and Description')),
                FieldPanel('domains'),
                ]

        superuser_panels = [
                MultiFieldPanel([
                    FieldPanel('name'),
                    FieldPanel('description'),
                    ], heading=_('Name and Description')),
                FieldPanel('organization'),
                FieldPanel('domains'),
                ]

        current_user = get_current_user()

        if current_user.is_superuser:
            custom_panels = superuser_panels
        else:
            custom_panels = basic_panels

        return ObjectList(custom_panels)

    def get_list_display(self, request):
        list_display = ['name', 'uuid']
        if request.user.is_superuser:
            list_display = ['name', 'uuid', 'organization']

        return list_display


modeladmin_register(WebfiltersAdmin)

