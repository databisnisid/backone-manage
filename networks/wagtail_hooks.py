from wagtail.contrib.modeladmin.options import (
    ModelAdmin, PermissionHelper, modeladmin_register)
#from wagtail import hooks
#from wagtail.snippets.models import register_snippet
#from wagtail.snippets.views.snippets import SnippetViewSet
from members.models import Members
#from wagtail.contrib.modeladmin.views import InspectView
from .models import Networks, NetworkRoutes, NetworkRules
from controllers.models import Controllers
#from config.utils import get_user
from wagtail.admin.panels import FieldPanel, InlinePanel, MultiFieldPanel, ObjectList
from django.utils.translation import gettext as _
from crum import get_current_user
#from wagtail.admin.forms import WagtailAdminPageForm
#from wagtail import hooks
#from django.core.exceptions import ObjectDoesNotExist
#from wagtail.snippets.models import register_snippet
#from wagtail.snippets.views.snippets import SnippetViewSet


'''
@hooks.register('construct_homepage_panels', order=1)
def add_user_org_panel(request, panels):
    user_org_panels = MultiFieldPanel([FieldPanel('user'), FieldPanel('organization')],
                                      heading=_('User and Organization'))
    if request.user.is_superuser:
        print(panels)
        panels.append(user_org_panels)
'''


class NetworksPermissionHelper(PermissionHelper):
    '''
    def user_can_list(self, user):
        result = False
        if user.has_perm('networks.view_networks'):
            result = True
        return result
    '''

    def user_can_create(self, user):
        result = True
        if user.is_superuser:
            result = False
            '''
            controllers = Controllers.objects.all().count()
            if controllers > 1:
                result = False
            else:
                result = True
            '''
        else:
            total_networks = Networks.objects.filter(organization=user.organization).count()
            if user.organization.features.number_of_network <= total_networks: 
                result = False
            '''
            else:
                result = False
            '''

        if not user.has_perm('networks.add_networks'):
            result = False

        return result

    '''
    def user_can_delete_obj(self, user, obj):
        result = False
        if user.has_perm('networks.delete_networks'):
            result = True
        return result

    def user_can_edit_obj(self, user, obj):
        result = False
        if user.has_perm('networks.change_networks'):
            result = True
        return result
    '''


class NetworkRulesPermissionHelper(PermissionHelper):
    '''
    def user_can_list(self, user):
        result = False
        if user.has_perm('networks.view_networkrules'):
            result = True
        return result
    '''

    def user_can_create(self, user):
        return False

    def user_can_delete_obj(self, user, obj):
        return False

    def user_can_edit_obj(self, user, obj):
        result = False
        if not user.is_superuser:
            result = True
        '''
            controllers = Controllers.objects.all().count()
            if controllers > 1:
                result = False
            else:
                result = True
        else:
            result = True
        '''

        if not user.has_perm('networks.change_networkrules'):
            result = False

        return result


class NetworkRoutesPermissionHelper(PermissionHelper):
    def user_can_delete_obj(self, user, obj):
        #print('Instance Delete', user)
        result = True
        if obj.gateway is None:
            return False
        else:
            if user.is_superuser:
                return False
                '''
                controllers = Controllers.objects.all().count()
                if controllers > 1:
                    return False
                else:
                    return True
            else:
                return True
                '''

        if not user.has_perm('networks.delete_networkroutes'):
            result = False

        return result

    def user_can_edit_obj(self, user, obj):
        return False

    '''
    def user_can_list(self, user):
        return True

    def user_can_create(self, user):
        if user.is_superuser:
            controllers = Controllers.objects.all().count()
            if controllers > 1:
                return False
            else:
                return True
        else:
            return True

    def user_can_delete_obj(self, user, obj):
        print('Instance Delete', user)
        if obj.gateway is None:
            return False
        else:
            if user.is_superuser:
                controllers = Controllers.objects.all().count()
                if controllers > 1:
                    return False
                else:
                    return True
            else:
                return True

    def user_can_edit_obj(self, user, obj):
        if user.is_superuser:
            controllers = Controllers.objects.all().count()
            if controllers > 1:
                return False
            else:
                return True
        else:
            return True
    '''

'''
class RestrictedFieldPanel(FieldPanel):
    def required_fields(self):
        current_user = get_current_user()
        #if self.request and self.request.user.is_superuser:
        print('FieldPanels', current_user)
        if current_user.is_superuser:
            return super().required_fields()
        return []
'''


class NetworksAdmin(ModelAdmin):
    model = Networks
    inspect_view_enabled = True
    menu_label = 'Networks'  # ditch this to use verbose_name_plural from model
    menu_icon = 'link'  # change as required
    add_to_settings_menu = False  # or True to add your model to the Settings sub-menu
    exclude_from_explorer = False # or True to exclude pages of this type from Wagtail's explorer view
    list_display = ('name', 'network_id', 'ip_allocation', 'controller', 'qr_network_id')
    #list_filter = ('name',)
    search_fields = ('name',)
    #list_filter = ('controller',)
    #base_form_class = NetworksForm
    permission_helper_class = NetworksPermissionHelper

    #def get_edit_handler(self, instance, request):
    def get_edit_handler(self):
        op_day_panels = [
            MultiFieldPanel([
                    FieldPanel('is_monday'), 
                    FieldPanel('is_tuesday'), 
                    FieldPanel('is_wednesday'), 
                    FieldPanel('is_thursday'), 
                    FieldPanel('is_friday'), 
                    FieldPanel('is_saturday'), 
                    FieldPanel('is_sunday'), 
                ])
            ]
        basic_panels = [
            MultiFieldPanel([FieldPanel('name'), FieldPanel('description')],
                            heading=_('Network Name and Description')),
            MultiFieldPanel([FieldPanel('ip_address_networks')],
                            heading=_('IP Network')),
        ]
        superuser_panels = [
            MultiFieldPanel([FieldPanel('name'), FieldPanel('description')],
                            heading=_('Network Name and Description')),
            MultiFieldPanel([FieldPanel('ip_address_networks')],
                            heading=_('IP Network')),
            MultiFieldPanel([FieldPanel('user')],
                            heading=_('Network Owner'))
        ]

        superuser_limit_panels = [
            MultiFieldPanel([FieldPanel('user')],
                            heading=_('Network Owner'))
        ]

        current_user = get_current_user()

        if current_user.is_superuser:
            controllers = Controllers.objects.all().count()
            if controllers > 1:
                custom_panels = superuser_limit_panels
            else:
                custom_panels = superuser_panels
        else:
            custom_panels = basic_panels

        return ObjectList(custom_panels)

    def get_queryset(self, request):
        current_user = get_current_user()
        if not current_user.is_superuser:
            if current_user.organization.is_no_org:
                return Networks.objects.filter(user=current_user)
            else:
                return Networks.objects.filter(organization=current_user.organization)
        else:
            return Networks.objects.all()

    def get_list_display(self, request):
        if request.user.is_superuser:
            list_display = ['name', 'network_id', 'ip_allocation', 'controller', 'qr_network_id']
        else:
            list_display = ['name', 'network_id', 'ip_allocation', 'qr_network_id']
        return list_display


class NetworkRoutesAdmin(ModelAdmin):
    model = NetworkRoutes
    #inspect_view_enabled = True
    menu_label = 'Network Routes'  # ditch this to use verbose_name_plural from model
    menu_icon = 'redirect'  # change as required
    add_to_settings_menu = False  # or True to add your model to the Settings sub-menu
    exclude_from_explorer = False # or True to exclude pages of this type from Wagtail's explorer view
    list_display = ('ip_network', 'get_member', 'network')
    list_filter = ('network',)
    search_fields = ('ip_network', 'gateway')
    ordering = ['network', 'gateway']
    permission_helper_class = NetworkRoutesPermissionHelper
    #base_form_class = NetworkRoutesForm

    panels = [
        MultiFieldPanel([FieldPanel('ip_network'), FieldPanel('gateway')],
                        heading=_('Target and Gateway')),
        FieldPanel('network'),
    ]

    def get_queryset(self, request):
        #current_user = get_user()
        current_user = get_current_user()
        if not request.user.is_superuser:
            if current_user.organization.is_no_org:
                return NetworkRoutes.objects.filter(user=current_user)
            else:
                return NetworkRoutes.objects.filter(organization=current_user.organization)
        else:
            return NetworkRoutes.objects.all()

'''
@hooks.register('construct_snippet_listing_buttons')
def remove_snippet_delete_button_networkrules(buttons, snippet, user, context=None):
    for button in buttons:
        index = buttons.index(button)

        if 'delete' in button.label.lower():
            if 'networks/networkrules/' in button.url:
                buttons.pop(index)
                break

@hooks.register('construct_snippet_listing_buttons')
def remove_snippet_edit_button_networkrules(buttons, snippet, user, context=None):
    for button in buttons:
        index = buttons.index(button)

        if 'edit' in button.label.lower():
            if user.is_superuser:
                buttons.pop(index)
                break
'''

class NetworkRulesAdmin(ModelAdmin):
#class NetworkRulesAdmin(SnippetViewSet):
    model = NetworkRules
    #inspect_view_enabled = True
    #index_template_name = 'networks/snippets/index.html'
    menu_label = 'Network Rules'  # ditch this to use verbose_name_plural from model
    menu_icon = 'tag'  # change as required
    #icon = 'tag'  # change as required
    add_to_settings_menu = False  # or True to add your model to the Settings sub-menu
    exclude_from_explorer = False # or True to exclude pages of this type from Wagtail's explorer view
    #add_to_admin_menu = True
    list_display = ('name', 'network',)
    #list_filter = ('network',)
    #menu_order = 999
    #search_fields = ('__str__',)
    #ordering = ['network', 'gateway']
    permission_helper_class = NetworkRulesPermissionHelper
    panels = [
        MultiFieldPanel([FieldPanel('network'),
            FieldPanel('rules_definition')],
                heading=_('Network Rules')),
    ]

    #def get_edit_handler(self, instance=None, request=None):
    '''
    def get_edit_handler(self):
        basic_panels = [
            MultiFieldPanel([FieldPanel('network'),
                             FieldPanel('rules_definition')],
                            heading=_('Network Rules')),
        ]

        advance_panels = [
            MultiFieldPanel([FieldPanel('network'),
                             FieldPanel('rules_definition'),
                             FieldPanel('rules')],
                            heading=_('Network Rules')),
        ]
        current_user = get_current_user()
        if current_user.is_superuser:
            return ObjectList(advance_panels)
        else:
            return ObjectList(basic_panels)
    '''

    def get_queryset(self, request):
        #current_user = get_user()
        current_user = get_current_user()
        if not current_user.is_superuser:
            if current_user.organization.is_no_org:
                return NetworkRules.objects.filter(user=current_user)
            else:
                return NetworkRules.objects.filter(organization=current_user.organization)
        else:
            return NetworkRules.objects.all()


# Now you just need to register your customised ModelAdmin class with Wagtail
modeladmin_register(NetworksAdmin)
modeladmin_register(NetworkRoutesAdmin)
modeladmin_register(NetworkRulesAdmin)
#register_snippet(NetworkRulesAdmin)


'''
class NetworksViewSet(SnippetViewSet):
    model = Networks
    search_fields = ['name']

register_snippet(NetworksViewSet)
'''
