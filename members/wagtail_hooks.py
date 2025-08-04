from django.core.exceptions import ObjectDoesNotExist
from wagtail.contrib.modeladmin.options import (
    ModelAdmin,
    modeladmin_register,
    ButtonHelper,
    PermissionHelper,
)
from wagtail.contrib.modeladmin.views import ModelFormView, InstanceSpecificView
from wagtail.snippets.models import register_snippet
from wagtail.snippets.views.snippets import SnippetViewSet

from accounts.customs import GroupOrganizationFilter
from accounts.models import GroupOrganizations
from licenses.utils import is_license_valid
from .models import Members, MemberPeers
from crum import get_current_user
from wagtail.admin.panels import FieldPanel, MultiFieldPanel, FieldRowPanel, ObjectList
from django.utils.translation import gettext as _
from django.conf import settings
from wagtail import hooks
from wagtailgeowidget import geocoders
from wagtailgeowidget.panels import GeoAddressPanel, GoogleMapsPanel

# from django.forms import HiddenInput
# from django.core.exceptions import ObjectDoesNotExist
# from wagtail.admin.forms import WagtailAdminModelForm
# from django import forms
# from networks.models import Networks
from licenses.utils import is_license_valid


"""
class MembersForm(WagtailAdminModelForm):
    network = forms.ModelChoiceField(queryset=Networks.objects, required=False, disabled=True)

    class Meta:
        model = Members
        fields = "__all__"

    def __init__(self, *args, **kwargs):

        self.request = kwargs.pop("request")
        self.instance = kwargs.pop("instance")
        print('Form ', self.request, self.instance)
        super(MembersForm, self).__init__(*args, **kwargs)

        #super().__init__(*args, **kwargs)
        #instance = getattr(self, 'instance', None)
        #print(instance)
        #if not instance.pk:
        #    # this is a NEW blog entry form - only allow title to be enabled, disable other fields
        #    self.fields['network'].widget.attrs['readonly'] = False
        #if instance.pk:
        #    self.fields['network'].widget.attrs['readonly'] = True
"""


class EditView(ModelFormView, InstanceSpecificView):
    pass


class MembersView(EditView):

    panels = [
        MultiFieldPanel(
            [FieldPanel("name"), FieldPanel("description")],
            heading=_("Network Name and Description"),
        ),
        # MultiFieldPanel([FieldPanel('member_id'), FieldPanel('network')],
        #                heading=_('Member ID and Network')),
        # MultiFieldPanel([FieldPanel('is_authorized'), FieldPanel('ipaddress')],
        #                heading=_('Authorization and IP Address')),
    ]


class MembersButtonHelper(ButtonHelper):

    # Define classes for our button, here we can set an icon for example
    # import_button_classnames = ["button-small", "icon", "icon-site"]
    # synchronize_classnames = ['button button-small button-primary']
    current_classnames = ["button button-small button-primary"]
    ssh_uri = "https://remotessh.backone.cloud"
    web_uri = "https://remoteweb.backone.cloud"
    # rtty_uri = 'https://remote.manage.backone.cloud'
    rtty_uri = settings.RTTY_URI

    """
    def synchronize_button(self, obj):
        if obj.configuration == '{}' and obj.is_authorized:
            print('Synchronize Configuration ', obj.name)
            obj.save()

        # Define a label for our button
        text = _('Synchronize')
        return {
            'url': self.url_helper.index_url, # Modify this to get correct action
            'label': text,
            'classname': self.finalise_classname(self.synchronize_classnames),
            'title': text,
        }
    """

    def ssh_button(self, obj):
        text = _("SSH")
        # ssh_uri_login = self.ssh_uri
        ssh_uri_login = self.rtty_uri

        """
        if obj.ipaddress:
            ssh_uri_login += '/?hostname=' + obj.ipaddress + '&username=root&password=SzBsMHIxajANCg==&term=xterm-256color&title='

        if obj.name:
            ssh_uri_login += obj.name.replace(' ', '-')
        """

        if obj.serialnumber():
            ssh_uri_login += "/rtty/" + obj.serialnumber()

        return {
            "url": ssh_uri_login,  # Modify this to get correct action
            "label": text,
            "classname": self.finalise_classname(self.current_classnames),
            "title": text,
        }

    def web_button(self, obj):
        text = _("WEB")
        # web_uri_login = self.web_uri
        web_uri_login = self.rtty_uri

        # if obj.ipaddress:
        #    web_uri_login += '/?hostname=' + obj.ipaddress
        if obj.serialnumber():
            web_uri_login += "/web/" + obj.serialnumber() + "/http/127.0.0.1:80/"

        return {
            "url": web_uri_login,  # Modify this to get correct action
            "label": text,
            "classname": self.finalise_classname(self.current_classnames),
            "title": text,
        }

    def get_buttons_for_obj(
        self, obj, exclude=None, classnames_add=None, classnames_exclude=None
    ):
        current_user = get_current_user()

        # is_ssh_web = True if obj.ipaddress else False
        is_ssh_web = True if obj.serialnumber() else False

        """
        This function is used to gather all available buttons.
        We append our custom button to the btns list.
        """
        buttons = super().get_buttons_for_obj(
            obj, exclude, classnames_add, classnames_exclude
        )
        """
        if 'synchronize_button' not in (exclude or []):
            if current_user.is_superuser:
                buttons.append(self.synchronize_button(obj))
            else:
                if current_user.organization.features.synchronize:
                    buttons.append(self.synchronize_button(obj))
        """

        if "ssh_button" not in (exclude or []) and obj.is_online() and is_ssh_web:
            if current_user.is_superuser:
                buttons.append(self.ssh_button(obj))
            else:
                if current_user.organization.features.ssh:
                    buttons.append(self.ssh_button(obj))

        if "web_button" not in (exclude or []) and obj.is_online() and is_ssh_web:
            if current_user.is_superuser:
                buttons.append(self.web_button(obj))
            else:
                if current_user.organization.features.web:
                    buttons.append(self.web_button(obj))

        return buttons


class MemberPeersPermissionHelper(PermissionHelper):
    def user_can_list(self, user):
        return True

    def user_can_create(self, user):
        return False

    def user_can_delete_obj(self, user, obj):
        return False

    def user_can_edit_obj(self, user, obj):
        return False


class MembersPermissionHelper(PermissionHelper):
    def user_can_list(self, user):
        result = True
        if not user.has_perm("members.view_members"):
            result = False

        return result

    def user_can_create(self, user):
        result = True
        total_members = Members.objects.filter(organization=user.organization).count()
        if not (user.organization.features.number_of_member > total_members):
            result = False

        if not user.has_perm("members.add_members"):
            result = False

        if user.is_superuser:
            result = False

        """ Check Group Organization """
        try:
            GroupOrganizations.objects.get(main_org=user.organization)
            result = False
        except ObjectDoesNotExist:
            pass

        """ Check License """
        if not is_license_valid(user):
            result = False

        return result

    def user_can_delete_obj(self, user, obj):
        result = True
        if not user.has_perm("members.delete_members"):
            result = False

        """ Check Group Organization """
        try:
            GroupOrganizations.objects.get(main_org=user.organization)
            result = False
        except ObjectDoesNotExist:
            pass

        """ Check License """
        if not is_license_valid(user):
            result = False

        return result

    def user_can_edit_obj(self, user, obj):
        result = True
        if not user.has_perm("members.change_members"):
            result = False

        if user.is_superuser:
            result = False

        """ Check Group Organization """
        try:
            GroupOrganizations.objects.get(main_org=user.organization)
            result = False
        except ObjectDoesNotExist:
            pass

        """ Check License """
        if not is_license_valid(user):
            result = False

        return result


class MembersAdmin(ModelAdmin):
    model = Members
    button_helper_class = MembersButtonHelper
    permission_helper_class = MembersPermissionHelper
    inspect_view_enabled = True
    menu_label = "Members"  # ditch this to use verbose_name_plural from model
    menu_icon = "list-ul"  # change as required
    add_to_settings_menu = False  # or True to add your model to the Settings sub-menu
    exclude_from_explorer = (
        False  # or True to exclude pages of this type from Wagtail's explorer view
    )

    list_per_page = 10

    list_export = (
        "name",
        "member_id",
        "ipaddress",
        "network",
        "address",
        "location",
        "get_routes_plain",
        "online_at",
        "offline_at",
    )
    list_display = (
        "member_name_with_address",
        "member_status",
        "model_release",
        "get_routes",
        "list_peers",
        "online_at",
        "offline_at",
    )
    list_filter = (
        "is_waf",
        "is_dpi",
        "is_authorized",
        "network",
        GroupOrganizationFilter,
    )
    search_fields = (
        "name",
        "member_id",
        "member_code",
        "ipaddress",
        "address",
        "mobile_number_first",
        "mqtt__serialnumber",
        "mqtt__model",
        "mqtt__uptime",
        "mqtt__release_version",
        "mqtt__hostname",
        "mqtt__quota_first",
    )

    create_template_name = "modeladmin/create.html"
    edit_template_name = "modeladmin/edit.html"

    def get_list_display(self, request):
        # current_user = get_current_user()
        current_user = request.user

        list_display = []
        list_display_default = [
            "member_name_with_address",
            "member_status",
            "model_release",
            "get_routes",
            "list_peers",
        ]
        list_display_superuser = [
            "member_name_with_address",
            "member_status",
            "model_release",
            "get_routes",
            "list_peers",
        ]
        list_display_simple = [
            "name",
            # "member_code",
            "address",
            "ipaddress",
            # "switchport_up",
            "online_status",
            "quota_first_simple",
        ]
        list_display_telkomsel = [
            "name",
            "member_code",
            "address",
            "ipaddress",
            "switchport_up",
            "online_status",
            "quota_vnstat",
        ]
        if current_user.organization.features.is_telkomsel:
            list_display = list_display_telkomsel
        elif current_user.organization.features.is_simple_list:
            list_display = list_display_simple
        elif current_user.is_superuser:
            list_display = list_display_superuser
        else:
            list_display = list_display_default

        if current_user.organization.features.online_offline:
            list_display.append("online_at")
            list_display.append("offline_at")
        # return super().get_list_display(request)

        if current_user.organization.features.is_lte_signal:
            list_display.append("rssi")

        return list_display

    def get_list_export(self, request):
        current_user = get_current_user()
        list_export = []
        list_export_default = [
            "member_name_with_address",
            "member_status",
            "model_release",
            "get_routes",
            "list_peers",
        ]
        list_export_telkomsel = [
            "name",
            "member_code",
            "address",
            "ipaddress",
            "switchport_up",
            "online_status",
            "quota_vnstat",
        ]
        list_export_simple = [
            "name",
            "member_code",
            "address",
            "ipaddress",
            "switchport_up",
            "online_status",
        ]

        if current_user.organization.features.is_export:
            if current_user.organization.features.is_telkomsel:
                list_export = list_export_telkomsel
            elif current_user.organization.features.is_simple_list:
                list_export = list_export_simple
            else:
                list_export = list_export_default

            if current_user.organization.features.online_offline:
                list_export.append("online_at")
                list_export.append("offline_at")

        return list_export
        # return super().get_list_export(request)

    def get_edit_handler(self):
        basic_panels = [
            # MultiFieldPanel([FieldPanel('name'), FieldPanel('description'), FieldPanel('online_at')],
            MultiFieldPanel(
                [
                    FieldPanel("name"),
                    FieldPanel("member_code"),
                    FieldPanel("description"),
                ],
                heading=_("Member Name, Code and Description"),
            ),
            MultiFieldPanel(
                [
                    FieldRowPanel([FieldPanel("member_id"), FieldPanel("network")]),
                ],
                heading=_("Member ID and Network"),
                classname="collapsed",
            ),
            # MultiFieldPanel([
            #    GeoAddressPanel("address", geocoder=geocoders.GOOGLE_MAPS),
            #    GoogleMapsPanel('location', address_field='address'),
            # ], _('Geo details')),
            # MultiFieldPanel([FieldPanel('is_authorized'), FieldPanel('ipaddress')],
            #                heading=_('Authorization and IP Address')),
        ]

        basic_no_network_panels = [
            MultiFieldPanel(
                [FieldPanel("name"), FieldPanel("description")],
                heading=_("Network Name and Description"),
            ),
            # MultiFieldPanel([FieldPanel('member_id'), FieldPanel('network')],
            #                heading=_('Member ID and Network')),
            # MultiFieldPanel([FieldPanel('is_authorized'), FieldPanel('ipaddress')],
            #                heading=_('Authorization and IP Address')),
        ]

        mobile_connect_panels = MultiFieldPanel(
            [FieldRowPanel([FieldPanel("mobile_number_first")])],
            heading=_("Mobile Connection"),
            classname="collapsed",
        )

        geolocation_panels = MultiFieldPanel(
            [
                GeoAddressPanel("address", geocoder=geocoders.GOOGLE_MAPS),
                GoogleMapsPanel("location", address_field="address"),
            ],
            heading=_("Geo Location"),
            classname="collapsed",
        )

        connection_panels = MultiFieldPanel(
            [FieldRowPanel([FieldPanel("online_at"), FieldPanel("offline_at")])],
            heading=_("Online/Offline"),
            classname="collapsed",
        )

        bridge_panels = MultiFieldPanel(
            [FieldRowPanel([FieldPanel("is_bridge"), FieldPanel("is_no_auto_ip")])],
            heading=_("Bridge Features"),
            classname="collapsed",
        )
        authorize_panels = MultiFieldPanel(
            [FieldPanel("is_authorized"), FieldPanel("ipaddress")],
            heading=_("Authorization and IP Address"),
            classname="collapsed",
        )
        ipaddress_panels = FieldPanel("ipaddress")

        tags_panels = MultiFieldPanel(
            [FieldPanel("tags")], heading=_("Tagging Features"), classname="collapsed"
        )
        dpi_panels = MultiFieldPanel(
            [FieldPanel("is_dpi")], heading=_("DPI Features"), classname="collapsed"
        )

        current_user = get_current_user()
        # print('Handler Instance', instance)
        # print('Handler Request', request)
        # if not instance.id:
        custom_panels = basic_panels
        # else:
        #    custom_panels = basic_no_network_panels

        if current_user.is_superuser:
            custom_panels.append(connection_panels)
            custom_panels.append(geolocation_panels)
            custom_panels.append(authorize_panels)
            custom_panels.append(mobile_connect_panels)
            custom_panels.append(bridge_panels)
            custom_panels.append(dpi_panels)
            custom_panels.append(tags_panels)
        else:
            if current_user.organization.features.online_offline:
                custom_panels.append(connection_panels)
            if current_user.organization.features.geolocation:
                custom_panels.append(geolocation_panels)
            if current_user.organization.features.authorize:
                custom_panels.append(authorize_panels)
            else:
                custom_panels.append(ipaddress_panels)
            if current_user.organization.features.mobile_connect:
                custom_panels.append(mobile_connect_panels)
            if current_user.organization.features.bridge:
                custom_panels.append(bridge_panels)
            if current_user.organization.features.is_dpi:
                custom_panels.append(dpi_panels)
            if current_user.organization.features.tags:
                custom_panels.append(tags_panels)

        return ObjectList(custom_panels)

    def get_queryset(self, request):
        # current_user = get_user()
        current_user = get_current_user()
        if not current_user.is_superuser:
            if current_user.organization.is_no_org:
                return Members.objects.filter(user=current_user)
            else:
                try:
                    """Check Group Organization"""
                    g_org = GroupOrganizations.objects.get(
                        main_org=current_user.organization
                    )
                    return Members.objects.filter(
                        organization__in=g_org.member_org.all()
                    )
                except ObjectDoesNotExist:
                    return Members.objects.filter(
                        organization=current_user.organization
                    )
        else:
            return Members.objects.all()


@hooks.register("construct_snippet_listing_buttons")
def remove_snippet_edit_button_memberpeers(buttons, snippet, user, context=None):
    for button in buttons:
        index = buttons.index(button)

        if "edit" in button.label.lower():
            if "members/memberpeers/" in button.url:
                buttons.pop(index)
                break


class MemberPeersAdmin(SnippetViewSet):
    # class MemberPeersAdmin(ModelAdmin):

    model = MemberPeers
    inspect_view_enabled = True
    # index_template_name = 'mqtt/snippets/index.html'
    menu_label = "MemberPeers"  # ditch this to use verbose_name_plural from model
    # add_to_settings_menu = False  # or True to add your model to the Settings sub-menu
    exclude_from_explorer = (
        False  # or True to exclude pages of this type from Wagtail's explorer view
    )
    list_display = ("member_id", "updated_at", "network")
    permission_helper_class = MemberPeersPermissionHelper
    list_filter = ("network",)
    # search_fields = ('name', 'member_id', 'ipaddress')
    # menu_icon = 'grip'
    # ordering = ['name']
    list_per_page = 50

    # Wagtail 5.1.1
    add_to_admin_menu = True
    search_fields = ("member_id",)
    menu_order = 999
    # list_per_page = 50
    # menu_icon = 'grip'  # change as required
    icon = "grip"  # change as required


modeladmin_register(MembersAdmin)
# modeladmin_register(MemberPeersAdmin)
register_snippet(MemberPeersAdmin)
