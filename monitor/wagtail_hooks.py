from wagtail.contrib.modeladmin.options import (
    ModelAdmin, ModelAdminGroup, modeladmin_register, ButtonHelper, PermissionHelper)
from wagtail.snippets.models import register_snippet
from wagtail.snippets.views.snippets import SnippetViewSet
from wagtail.contrib.modeladmin.views import ModelFormView, InstanceSpecificView
from .models import MemberProblems, MonitorItems, MonitorRules, MemberProblemsDone
from crum import get_current_user
from wagtail.admin.panels import FieldPanel, InlinePanel, MultiFieldPanel, FieldRowPanel, ObjectList
from django.utils.translation import gettext as _
from django.conf import settings
from django.utils import timezone
#from datetime import datetime, timedelta


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
        return True


class MemberProblemsDoneHelper(PermissionHelper):
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
    #menu_icon = 'tick' # Wagtail 4.2
    menu_icon = 'check' # Wagtail 5.0
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
    #inspect_view_enabled = True

    #list_display = ('member', 'get_network' ,'problem', 'duration_text_undone')
    list_display = ('member', 'problem_duration_start', 'get_update_progress')
    search_fields = ('member__name', 'problem__name', 'member__member_id')

    panels = [
        MultiFieldPanel([
            FieldRowPanel([
                FieldPanel('start_at', read_only=True),
            ]),
            FieldRowPanel([
                FieldPanel('member', read_only=True),
                FieldPanel('problem', read_only=True, heading=_('Reason')),
            ])], heading=_('Problem')),
        InlinePanel('member_problems', heading=_('Updates Progress')),
    ]

    def get_queryset(self, request):
        current_user = get_current_user()
        #problem_time = datetime.now() - timedelta(seconds=settings.MONITOR_DELAY)
        problem_time = timezone.now() - timezone.timedelta(seconds=settings.MONITOR_DELAY)
        if not current_user.is_superuser:
            if current_user.organization.is_no_org:
                #return MemberProblems.objects.filter(member__user=current_user)
                return MemberProblems.unsolved.filter(member__user=current_user, start_at__lt=problem_time).order_by('start_at')
            else:
                return MemberProblems.unsolved.filter(member__organization=current_user.organization, start_at__lt=problem_time).order_by('start_at')
        else:
            return MemberProblems.unsolved.filter(start_at__lt=problem_time).order_by('start_at')


class MemberProblemsHistoryAdmin(ModelAdmin):
    model = MemberProblemsDone
    permission_helper_class = MemberProblemsDoneHelper
    menu_label = 'History'
    menu_icon = 'tick-inverse'
    add_to_settings_menu = False
    exclude_from_explorer = False

    #list_display = ('member', 'problem', 'duration_text', 'start_at', 'end_at')
    list_display = ('member', 'problem_duration_start_end', 'get_update_progress')
    search_fields = ('member__name', 'problem__name', 'member__member_id')

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
