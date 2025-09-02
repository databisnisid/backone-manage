from wagtail.contrib.modeladmin.options import (
    ModelAdmin,
    ModelAdminGroup,
    PermissionHelper,
    modeladmin_register,
)
from wagtail.admin.panels import FieldPanel, MultiFieldPanel, FieldRowPanel
from .models import Features, LicenseFeatures
from django.utils.translation import gettext_lazy as _
from .models import Organizations, GroupOrganizations


class AccountsPermissionHelper(PermissionHelper):
    """

    def user_can_list(self, user):
        return True

    def user_can_create(self, user):
        if user.is_superuser:
            return True
        else:
            return False
    """

    def user_can_delete_obj(self, user, obj):
        if obj.id == 1:
            return False
        else:
            return True

    """
    def user_can_edit_obj(self, user, obj):
        return False
    """


class LicenseFeaturesPermissionHelper(PermissionHelper):
    def user_can_list(self, user):
        return True

    def user_can_create(self, user):
        return False

    def user_can_delete_obj(self, user, obj):
        return False

    def user_can_edit_obj(self, user, obj):
        return False


class OrganizationsAdmin(ModelAdmin):
    model = Organizations
    # button_helper_class = ControllerButtonHelper   # Uncomment this to enable button
    # inspect_view_enabled = True
    menu_label = "Organizations"  # ditch this to use verbose_name_plural from model
    menu_icon = "group"  # change as required
    add_to_settings_menu = True  # or True to add your model to the Settings sub-menu
    exclude_from_explorer = (
        False  # or True to exclude pages of this type from Wagtail's explorer view
    )
    list_display = ("name", "features", "controller", "uuid", "site")
    search_fields = ("name", "features")
    permission_helper_class = AccountsPermissionHelper

    panels = [
        MultiFieldPanel(
            [FieldPanel("name"), FieldPanel("features")], heading=_("Name and Features")
        ),
        FieldPanel("controller"),
        FieldPanel("is_no_org"),
        MultiFieldPanel(
            [
                FieldPanel("site"),
                FieldPanel("logo"),
                FieldPanel("logo_dashboard"),
                FieldPanel("favicon"),
            ],
            heading=_("Site Customization"),
        ),
    ]

    def __init__(self, *args, **kwargs):
        # request = kwargs.get('request')
        # print('User ', self.current_user)
        # self.inspect_view_enabled = True
        super().__init__(*args, **kwargs)


class GroupOrganizationsAdmin(ModelAdmin):
    model = GroupOrganizations
    # button_helper_class = ControllerButtonHelper   # Uncomment this to enable button
    # inspect_view_enabled = True
    menu_label = (
        "Group Organizations"  # ditch this to use verbose_name_plural from model
    )
    menu_icon = "group"  # change as required
    add_to_settings_menu = True  # or True to add your model to the Settings sub-menu
    exclude_from_explorer = (
        False  # or True to exclude pages of this type from Wagtail's explorer view
    )
    list_display = ("name", "main_org", "member_org_list")
    panels = [
        FieldPanel("name"),
        FieldPanel("main_org"),
        FieldPanel("member_org"),
    ]


class FeaturesAdmin(ModelAdmin):
    model = Features
    menu_label = "Features"  # ditch this to use verbose_name_plural from model
    menu_icon = "snippet"  # change as required
    add_to_settings_menu = True  # or True to add your model to the Settings sub-menu
    exclude_from_explorer = (
        False  # or True to exclude pages of this type from Wagtail's explorer view
    )
    list_display = ("name", "description", "uuid")
    list_filter = ("name",)
    search_fields = ("name",)
    # ordering = ['name']
    permission_helper_class = AccountsPermissionHelper

    panels = [
        MultiFieldPanel(
            [FieldPanel("name"), FieldPanel("description")],
            heading=_("Name and Description"),
        ),
        MultiFieldPanel(
            [
                FieldRowPanel(
                    [FieldPanel("network_multi_ip"), FieldPanel("network_rules")],
                    classname="collapsible collapsed",
                ),
                FieldPanel("number_of_network"),
            ],
            heading=_("Network Features"),
        ),
        MultiFieldPanel(
            [
                FieldRowPanel([FieldPanel("authorize"), FieldPanel("member_multi_ip")]),
                FieldRowPanel([FieldPanel("bridge"), FieldPanel("tags")]),
                FieldPanel("number_of_member"),
            ],
            # FieldRowPanel([FieldPanel('synchronize')])],
            heading=_("Member Features"),
        ),
        MultiFieldPanel(
            [FieldRowPanel([FieldPanel("web"), FieldPanel("ssh")])],
            heading=_("Remote Access Features"),
        ),
        MultiFieldPanel([FieldRowPanel([FieldPanel("is_dpi")])], heading=_("DPI")),
        MultiFieldPanel(
            [
                FieldRowPanel(
                    [FieldPanel("is_webfilter"), FieldPanel("is_webfilter_multinet")]
                )
            ],
            heading=_("Web Filters"),
        ),
        MultiFieldPanel(
            [
                FieldRowPanel(
                    [FieldPanel("geolocation"), FieldPanel("online_offline")]
                ),
                FieldRowPanel([FieldPanel("is_export"), FieldPanel("mobile_connect")]),
                FieldRowPanel([FieldPanel("map_dashboard"), FieldPanel("is_nms")]),
                FieldRowPanel(
                    [FieldPanel("is_simple_list"), FieldPanel("is_lte_signal")]
                ),
                FieldRowPanel([FieldPanel("is_deauth_timer")]),
            ],
            heading=_("Additional Features"),
        ),
        MultiFieldPanel(
            [FieldRowPanel([FieldPanel("is_telkomsel")])], heading=_("Project Related")
        ),
    ]


class LicenseFeaturesAdmin(ModelAdmin):
    model = LicenseFeatures
    menu_label = "Features"  # ditch this to use verbose_name_plural from model
    menu_icon = "snippet"  # change as required
    add_to_settings_menu = True  # or True to add your model to the Settings sub-menu
    inspect_view_enabled = True
    exclude_from_explorer = (
        False  # or True to exclude pages of this type from Wagtail's explorer view
    )
    list_display = ("name", "description", "uuid")
    list_filter = ("name",)
    search_fields = ("name",)
    # ordering = ['name']
    permission_helper_class = AccountsPermissionHelper

    panels = [
        MultiFieldPanel(
            [FieldPanel("name"), FieldPanel("description")],
            heading=_("Name and Description"),
        ),
        MultiFieldPanel(
            [
                FieldRowPanel(
                    [
                        FieldPanel("network_multi_ip", read_only=True),
                        FieldPanel("network_rules", read_only=True),
                    ],
                    classname="collapsible collapsed",
                ),
                FieldPanel("number_of_network", read_only=True),
            ],
            heading=_("Network Features"),
        ),
        MultiFieldPanel(
            [
                FieldRowPanel(
                    [
                        FieldPanel("authorize", read_only=True),
                        FieldPanel("member_multi_ip", read_only=True),
                    ]
                ),
                FieldRowPanel(
                    [
                        FieldPanel("bridge", read_only=True),
                        FieldPanel("tags", read_only=True),
                    ]
                ),
                FieldPanel("number_of_member", read_only=True),
            ],
            # FieldRowPanel([FieldPanel('synchronize')])],
            heading=_("Member Features"),
        ),
        MultiFieldPanel(
            [
                FieldRowPanel(
                    [
                        FieldPanel("web", read_only=True),
                        FieldPanel("ssh", read_only=True),
                    ]
                )
            ],
            heading=_("Remote Access Features"),
        ),
        MultiFieldPanel(
            [FieldRowPanel([FieldPanel("is_dpi", read_only=True)])], heading=_("DPI")
        ),
        MultiFieldPanel(
            [
                FieldRowPanel(
                    [
                        FieldPanel("is_webfilter", read_only=True),
                        FieldPanel("is_webfilter_multinet", read_only=True),
                    ]
                )
            ],
            heading=_("Web Filters"),
        ),
        MultiFieldPanel(
            [
                FieldRowPanel(
                    [
                        FieldPanel("geolocation", read_only=True),
                        FieldPanel("online_offline", read_only=True),
                    ]
                ),
                FieldRowPanel(
                    [
                        FieldPanel("is_export", read_only=True),
                        FieldPanel("mobile_connect", read_only=True),
                    ]
                ),
                FieldRowPanel(
                    [
                        FieldPanel("map_dashboard", read_only=True),
                        FieldPanel("is_nms", read_only=True),
                    ]
                ),
                FieldRowPanel(
                    [
                        FieldPanel("is_simple_list", read_only=True),
                        FieldPanel("is_lte_signal", read_only=True),
                    ]
                ),
                FieldRowPanel([FieldPanel("is_deauth_timer", read_only=True)]),
            ],
            heading=_("Additional Features"),
        ),
        MultiFieldPanel(
            [FieldRowPanel([FieldPanel("is_telkomsel", read_only=True)])],
            heading=_("Project Related"),
        ),
    ]


class AccountsGroup(ModelAdminGroup):
    menu_label = "Accounts"
    menu_icon = "folder-open-inverse"  # change as required
    menu_order = 200  # will put in 3rd place (000 being 1st, 100 2nd)
    items = (
        OrganizationsAdmin,
        GroupOrganizationsAdmin,
        FeaturesAdmin,
        LicenseFeaturesAdmin,
    )


# Now you just need to register your customised ModelAdmin class with Wagtail
# modeladmin_register(AccountsGroup)
modeladmin_register(LicenseFeaturesAdmin)
modeladmin_register(FeaturesAdmin)
modeladmin_register(OrganizationsAdmin)
modeladmin_register(GroupOrganizationsAdmin)
