from wagtail.contrib.modeladmin.options import (
    ModelAdmin, ModelAdminGroup, modeladmin_register, ButtonHelper, PermissionHelper)
from wagtail.contrib.modeladmin.views import ModelFormView, InstanceSpecificView

from .models import MemberProblems, MonitorItems, MonitorRules
from crum import get_current_user
from wagtail.admin.panels import FieldPanel, MultiFieldPanel, FieldRowPanel, ObjectList
from django.utils.translation import gettext as _



class MemberProblemsButtonHelper(ButtonHelper):
    pass


class MonitorItemsAdmin(ModelAdmin):
    model = MonitorItems
    menu_label = 'Items'
    menu_icon = 'list-ul'
    list_display = ('name', 'item_id')


class MonitorRulesAdmin(ModelAdmin):
    model = MonitorRules
    menu_label = 'Rules'
    menu_icon = 'tick'
    list_display = ('name', 'item', 'item_threshold')


class MemberProblemsAdmin(ModelAdmin):
    model = MemberProblems
    menu_label = 'Monitor'
    menu_icon = 'cog'
    add_to_settings_menu = False
    exclude_from_explorer = False

    list_display = ('member', 'problem')


class MonitorAdminGroup(ModelAdminGroup):
    menu_label = _("Monitor")
    items = (MonitorItemsAdmin, MonitorRulesAdmin, MemberProblemsAdmin)


#modeladmin_register(MemberProblemsAdmin)
#modeladmin_register(MonitorItemsAdmin)
#modeladmin_register(MonitorRulesAdmin)
modeladmin_register(MonitorAdminGroup)
