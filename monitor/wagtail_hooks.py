from wagtail.contrib.modeladmin.options import (
    ModelAdmin, modeladmin_register, ButtonHelper, PermissionHelper)
from wagtail.contrib.modeladmin.views import ModelFormView, InstanceSpecificView

from .models import MemberProblems
from crum import get_current_user
from wagtail.admin.panels import FieldPanel, MultiFieldPanel, FieldRowPanel, ObjectList
from django.utils.translation import gettext as _



class MemberProblemsButtonHelper(ButtonHelper):
    pass


class MemberProblemsAdmin(ModelAdmin):
    model = MemberProblems
    menu_label = 'Monitor'
    menu_icon = 'list-ul'
    add_to_settings_menu = False
    exclude_from_explorer = False

    list_display = ('member', 'problem')


modeladmin_register(MemberProblemsAdmin)
