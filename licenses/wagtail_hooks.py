from wagtail.contrib.modeladmin.helpers import ButtonHelper
from wagtail.contrib.modeladmin.options import (
    ModelAdmin,
    ModelAdminGroup,
    ObjectList,
    PermissionHelper,
    modeladmin_register,
)
from wagtail.admin.panels import FieldPanel, MultiFieldPanel, FieldRowPanel
from django.utils.translation import gettext_lazy as _
from .models import Licenses
from accounts.models import Organizations
from crum import get_current_user
from django.urls import reverse


class LicensesButtonHelper(ButtonHelper):

    current_classnames = ["button button-small button-primary"]

    def json_button(self, obj):
        text = _("Download License")
        # obj_id = obj.id
        button_url = reverse("json_download", args=[obj.id])

        return {
            "url": button_url,
            "label": text,
            "classname": self.finalise_classname(self.current_classnames),
            "title": text,
        }

    def get_buttons_for_obj(
        self, obj, exclude=None, classnames_add=None, classnames_exclude=None
    ):
        buttons = super().get_buttons_for_obj(
            obj, exclude, classnames_add, classnames_exclude
        )
        if "json_button" not in (exclude or []):
            buttons.append(self.json_button(obj))

        return buttons


class LicensesPermissionHelper(PermissionHelper):
    """

    def user_can_list(self, user):
        return True
    """

    def user_can_create(self, user):
        if user.is_superuser:
            if (
                Licenses.objects.all().count()
                < Organizations.objects.filter(is_no_org=False).count()
            ):
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

    """
    def user_can_edit_obj(self, user, obj):
        return False
    """


class LicensesAdmin(ModelAdmin):
    model = Licenses
    button_helper_class = LicensesButtonHelper  # Uncomment this to enable button
    # inspect_view_enabled = True
    menu_label = "License"  # ditch this to use verbose_name_plural from model
    menu_icon = "key"  # change as required
    add_to_settings_menu = True  # or True to add your model to the Settings sub-menu
    exclude_from_explorer = (
        False  # or True to exclude pages of this type from Wagtail's explorer view
    )
    list_display = (
        "node_id",
        "get_organization_uuid",
        "get_controller_token",
        "organization",
        "get_license_time",
        "get_license_msg",
    )
    # search_fields = ('node_id', )
    permission_helper_class = LicensesPermissionHelper

    panels = [
        FieldPanel("node_id", read_only=True),
        FieldPanel("organization"),
        FieldPanel("license_features", read_only=True),
    ]
    """
    panels = [
        FieldPanel('node_id', read_only=True),
        FieldPanel('organization'),
        MultiFieldPanel([
            FieldPanel('license_key'),
            FieldPanel('license_string'),
            ], heading=_('License'))
    ]
    """

    def get_list_display(self, request):
        if request.user.is_superuser:
            # list_display = ('node_id', 'get_organization_uuid', 'get_controller_token', 'organization', 'get_license_time', 'get_license_msg',)
            list_display = (
                "node_id",
                "get_organization_uuid",
                "organization",
                "get_license_time",
                "get_license_msg",
            )
        else:
            list_display = (
                "node_id",
                "organization",
                "get_license_time",
                "get_license_msg",
            )

        return list_display

    def get_edit_handler(self):
        superuser_panels = [
            FieldPanel("node_id", read_only=True),
            FieldPanel("organization"),
        ]

        admin_panels = [
            FieldPanel("node_id", read_only=True),
            FieldPanel("organization", read_only=True),
        ]

        current_user = get_current_user()
        if current_user.is_superuser:
            return ObjectList(superuser_panels)
        else:
            return ObjectList(admin_panels)

    def get_queryset(self, request):
        if request.user.is_superuser:
            qs = Licenses.objects.all()

        else:
            if request.user.organization:
                qs = Licenses.objects.filter(organization=request.user.organization)
            else:
                qs = Licenses.objects.none()

        return qs

    """ Working INIT modeladmin """
    """ Not Really Working. Need more test """
    """
    def __init__(self, *args, **kwargs):
        self.inspect_view_enabled = False
        super(LicensesAdmin, self).__init__(*args, **kwargs)
    """


modeladmin_register(LicensesAdmin)
