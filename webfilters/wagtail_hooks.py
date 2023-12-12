from django.core.exceptions import MultipleObjectsReturned, ObjectDoesNotExist
from wagtail.contrib.modeladmin.options import (
    ModelAdmin, ModelAdminGroup, PermissionHelper, modeladmin_register)
from .models import WebFilters, WebFiltersOrg, WebFiltersMembers
from wagtail.admin.panels import FieldPanel, InlinePanel, MultiFieldPanel, ObjectList, FieldRowPanel
from django.utils.translation import gettext as _
from crum import get_current_user



class WebFiltersOrgAdmin(ModelAdmin):
    model = WebFiltersOrg
    menu_label = 'Org and Network'  # ditch this to use verbose_name_plural from model
    menu_icon = 'resubmit'  # change as required
    add_to_settings_menu = False  # or True to add your model to the Settings sub-menu
    exclude_from_explorer = False # or True to exclude pages of this type from Wagtail's explorer view
    list_display = ('organization', 'network')
    #base_form_class = NetworksForm


class WebfiltersPermissionHelper(PermissionHelper):
    def user_can_list(self, user):
        return True

    def user_can_create(self, user):
        if user.is_superuser:
            return True
        else:
            return False

    def user_can_delete_obj(self, user, obj):
        if user.is_superuser:
            return True
        else:
            return False

    def user_can_edit_obj(self, user, obj):
        return True


class WebfiltersAdmin(ModelAdmin):
    model = WebFilters
    inspect_view_enabled = True
    menu_label = 'WebFilters'  # ditch this to use verbose_name_plural from model
    menu_icon = 'globe'  # change as required
    add_to_settings_menu = False  # or True to add your model to the Settings sub-menu
    exclude_from_explorer = False # or True to exclude pages of this type from Wagtail's explorer view
    list_display = ('name', 'domains', 'uuid')
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
                if request.user.organization.features.is_webfilter:
                    if request.user.organization.features.is_webfilter_multinet:
                        return WebFilters.objects.filter(organization=request.user.organization)
                    else:
                        try:
                            network = WebFiltersOrg.objects.get(organization=request.user.organization)
                            return WebFilters.objects.filter(network=network.network)
                        except ObjectDoesNotExist:
                            return WebFilters.objects.none()
        else:
            return WebFilters.objects.all()

    def get_edit_handler(self):
        basic_panels = [
                MultiFieldPanel([
                    FieldPanel('name'),
                    FieldPanel('description'),
                    ], heading=_('Name and Description')),
                FieldPanel('is_default_block'),
                FieldRowPanel([
                    FieldPanel('domains'),
                    FieldPanel('domains_white'),
                    ])
                ]

        superuser_panels = [
                MultiFieldPanel([
                    FieldPanel('name'),
                    FieldPanel('description'),
                    ], heading=_('Name and Description')),
                FieldPanel('organization'),
                FieldPanel('network'),
                FieldPanel('is_default_block'),
                FieldRowPanel([
                    FieldPanel('domains'),
                    FieldPanel('domains_white'),
                    ])
                ]

        current_user = get_current_user()

        if current_user.is_superuser:
            custom_panels = superuser_panels
        else:
            custom_panels = basic_panels

        return ObjectList(custom_panels)

    def get_list_display(self, request):
        list_display = ['name', 'is_default_block', 'domains', 'domains_white', 'uuid']
        if request.user.is_superuser:
            list_display = ['name', 'is_default_block', 'domains', 'domains_white', 'uuid', 'network', 'organization']

        return list_display


class WebFiltersMembersAdmin(ModelAdmin):
    model = WebFiltersMembers
    menu_label = 'Member WebFilter'  # ditch this to use verbose_name_plural from model
    menu_icon = 'upload'  # change as required
    add_to_settings_menu = False  # or True to add your model to the Settings sub-menu
    exclude_from_explorer = False # or True to exclude pages of this type from Wagtail's explorer view
    list_display = ('member', 'webfilter')
    #search_fields = ('organization', 'uuid',)
    #list_filter = ('controller',)
    #base_form_class = NetworksForm
    #permission_helper_class = WebfiltersPermissionHelper

    def get_queryset(self, request):
        if request.user.is_superuser:
            return WebFiltersMembers.objects.all()
        else:
            if request.user.organization.features.is_webfilter:
                if request.user.organization.features.is_webfilter_multinet:
                    return WebFiltersMembers.objects.filter(member__organization=request.user.organization)
                else:
                    try:
                        network = WebFiltersOrg.objects.get(organization=request.user.organization)
                        return WebFiltersMembers.objects.filter(member__network=network.network)
                    except ObjectDoesNotExist or MultipleObjectsReturned:
                        return WebFiltersMembers.objects.none()
            else:
                return WebFiltersMembers.objects.none()

#modeladmin_register(WebfiltersAdmin)

class WebFiltersAdminGroup(ModelAdminGroup):
    menu_label = _("WAF")
    menu_icon = 'download'
    items = (WebFiltersOrgAdmin, WebfiltersAdmin, WebFiltersMembersAdmin)


modeladmin_register(WebFiltersAdminGroup)

