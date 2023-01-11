from wagtail.contrib.modeladmin.options import (
    ModelAdmin, ModelAdminGroup, modeladmin_register, ButtonHelper, PermissionHelper)
from wagtail.contrib.modeladmin.views import ModelFormView, InstanceSpecificView

from .models import MemberProblems, MonitorItems, MonitorRules, MemberProblemsDone
from crum import get_current_user
from wagtail.admin.panels import FieldPanel, MultiFieldPanel, FieldRowPanel, ObjectList
from django.utils.translation import gettext as _
from django.conf import settings


class MemberProblemsButtonHelper(ButtonHelper):

    # Define classes for our button, here we can set an icon for example
    #import_button_classnames = ["button-small", "icon", "icon-site"]
    current_classnames = ['button button-small button-primary']

    def check_button(self, obj):
        # Define a label for our button
        text = _('Check')
        return {
            'url': '/members/members/?q=' + obj.member.member_id,
            'label': text,
            'classname': self.finalise_classname(self.current_classnames),
            'title': text,
        }

    def get_buttons_for_obj(
        self, obj, exclude=None, classnames_add=None, classnames_exclude=None
    ):
        current_user = get_current_user()

        """
        This function is used to gather all available buttons.
        We append our custom button to the btns list.
        """
        buttons = super().get_buttons_for_obj(
            obj, exclude, classnames_add, classnames_exclude
        )
        if 'check_button' not in (exclude or []):
            if current_user.is_superuser:
                buttons.append(self.check_button(obj))
            else:
                #if current_user.organization.features.synchronize:
                buttons.append(self.check_button(obj))

        return buttons


class MemberProblemsHelper(PermissionHelper):
    def user_can_list(self, user):
        return True

    def user_can_create(self, user):
        return False

    def user_can_delete_obj(self, user, obj):
        return False

    def user_can_edit_obj(self, user, obj):
        return False



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

    panels = [
        MultiFieldPanel([FieldPanel('name')], heading=_('Name')),
        MultiFieldPanel(
            [
                FieldPanel('item'),
                FieldPanel('item_threshold')
            ],
            heading=_('Item Detail'))
    ]
    '''
    def get_edit_handler(self, instance, request):
        basic_panels = [
            MultiFieldPanel([FieldPanel('name')], heading=_('Name')),
            MultiFieldPanel(
                [
                    FieldPanel('item'),
                    FieldPanel('item_threshold')
                ],
                heading=_('Item Detail'))
        ]

        user_org_panels = [
            MultiFieldPanel(
                [
                    FieldPanel('user'),
                    FieldPanel('organization')
                ],
                heading=_('User and Organization')
            )
        ]

        custom_panels = basic_panels

        current_user = get_current_user()

        if current_user.is_superuser:
            custom_panels.append(user_org_panels)

        return ObjectList(custom_panels)

    '''

    def get_queryset(self, request):
        current_user = get_current_user()
        if not current_user.is_superuser:
            if current_user.organization.is_no_org:
                return MonitorRules.objects.filter(user=current_user)
            else:
                return MonitorRules.objects.filter(organization=current_user.organization)
        else:
            return MonitorRules.objects.all()


class MemberProblemsAdmin(ModelAdmin):
    model = MemberProblems
    button_helper_class = MemberProblemsButtonHelper
    permission_helper_class = MemberProblemsHelper
    menu_label = 'Monitor'
    menu_icon = 'cog'
    add_to_settings_menu = False
    exclude_from_explorer = False

    list_display = ('member', 'problem', 'duration_text_undone')

    def get_queryset(self, request):
        current_user = get_current_user()
        if not current_user.is_superuser:
            if current_user.organization.is_no_org:
                #return MemberProblems.objects.filter(member__user=current_user)
                return MemberProblems.unsolved.filter(member__user=current_user)
            else:
                return MemberProblems.unsolved.filter(member__organization=current_user.organization)
        else:
            return MemberProblems.unsolved.all()

class MemberProblemsHistoryAdmin(ModelAdmin):
    model = MemberProblemsDone
    permission_helper_class = MemberProblemsHelper
    menu_label = 'History'
    menu_icon = 'tick-inverse'
    add_to_settings_menu = False
    exclude_from_explorer = False

    list_display = ('member', 'problem', 'duration_text', 'start_at', 'end_at')

    def get_queryset(self, request):
        current_user = get_current_user()
        if not current_user.is_superuser:
            if current_user.organization.is_no_org:
                #return MemberProblems.objects.filter(member__user=current_user)
                return MemberProblemsDone.objects.filter(member__user=current_user, duration__gt=settings.MONITOR_DELAY).order_by('-duration')
            else:
                return MemberProblemsDone.objects.filter(member__organization=current_user.organization, duration__gt=settings.MONITOR_DELAY).order_by('-duration')
        else:
            return MemberProblemsDone.objects.filter(duration__gt=settings.MONITOR_DELAY).order_by('-duration')


class MonitorAdminGroup(ModelAdminGroup):
    menu_label = _("Monitor")
    items = (MonitorItemsAdmin, MonitorRulesAdmin,
             MemberProblemsAdmin, MemberProblemsHistoryAdmin)


modeladmin_register(MonitorAdminGroup)
