from django.core.validators import ValidationError
from django.db import models
from django.utils.html import format_html
from crum import get_current_user
from accounts.models import User, Organizations
from mqtt.models import Mqtt
from members.models import Members
from django.utils.translation import gettext as _
from django.utils import timezone
from config.utils import readable_timedelta_seconds
from modelcluster.models import ClusterableModel
from modelcluster.fields import ParentalKey
from wagtail.admin.panels import FieldPanel, InlinePanel, MultiFieldPanel, FieldRowPanel, ObjectList

DURATION_RED_ALERT = 3600

class MonitorItems(models.Model):
    name = models.CharField(_('Item'), max_length=50)
    item_id = models.CharField(_('Item Keyword'), max_length=50, unique=True)

    class Meta:
        db_table = 'monitor_items'
        verbose_name = _('Monitor Item')
        verbose_name_plural = _('Monitor Items')

    created_at = models.DateTimeField(auto_now=False, auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True, auto_now_add=False)

    def __str__(self):
        return '{}'.format(self.name)

    def save(self):
        self.item_id = self.item_id.lower()

        return super(MonitorItems, self).save()


class MonitorRules(models.Model):
    '''
    def limit_choices_to_current_user():
        user = get_current_user()
        if not user.is_superuser:
            if user.organization.is_no_org:
                return {'user': user}
            else:
                return {'organization': user.organization}
        else:
            return {}
    '''
    name = models.CharField(_('Problem Name'), max_length=100)
    item = models.ForeignKey(
        MonitorItems,
        on_delete=models.SET_NULL,
        verbose_name=_('Item'),
        null=True

    )
    item_threshold = models.FloatField(
        _('Threshold'),
        default=0,
        help_text='Float Value')

    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        verbose_name=_('Owner'),
        null=True
    )
    organization = models.ForeignKey(
        Organizations,
        on_delete=models.SET_NULL,
        verbose_name=_('Organization'),
        null=True
    )

    created_at = models.DateTimeField(auto_now=False, auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True, auto_now_add=False)

    class Meta:
        db_table = 'monitor_rules'
        verbose_name = _('Monitor Rule')
        verbose_name_plural = _('Monitor Rules')

    def __str__(self):
        return '{}'.format(self.name)

    def save(self):
        if self.user is None:
            self.user = get_current_user()

        #print('MonitorRules Model', self.user)

        self.organization = self.user.organization

        return super(MonitorRules, self).save()


class MemberProblemManagerUndone(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(
            is_done=False
        ).exclude(member=None)

class MemberProblemManagerDone(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(
            is_done=True
        ).exclude(member=None)


#class MemberProblems(models.Model):
class MemberProblems(ClusterableModel):
    member = models.ForeignKey(
        Members,
        on_delete=models.SET_NULL,
        verbose_name=_('Member'),
        null=True
    )
    problem = models.ForeignKey(
        MonitorRules,
        on_delete=models.RESTRICT,
        verbose_name=_('Problem')
    )

    is_done = models.BooleanField(_('Problem Solved'), default=False)
    duration = models.IntegerField(_('Duration'), default=0)

    #objects = MemberProblemManagerUndone()
    unsolved = MemberProblemManagerUndone()
    solved = MemberProblemManagerDone()
    alls = models.Manager()
    objects = models.Manager()

    start_at = models.DateTimeField(auto_now=False, auto_now_add=True)
    end_at = models.DateTimeField(auto_now=True, auto_now_add=False)

    class Meta:
        db_table = 'member_problem'
        verbose_name = _('Member Problem')
        verbose_name_plural = _('Member Problems')

    def __str__(self):
        return '{}'.format(self.member)

    def save(self):
        if self.is_done:
            delta = timezone.now() - timezone.localtime(self.start_at)
            self.duration = delta.seconds

        return super(MemberProblems, self).save()


    def duration_text_undone(self):
        delta = timezone.now() - timezone.localtime(self.start_at)

        color = 'black'
        if delta.seconds > DURATION_RED_ALERT:
            color = 'red'

        duration_html = format_html("<span style='style: {}'>{}</span>",
                                    color, readable_timedelta_seconds(delta.seconds))
        return duration_html
    duration_text_undone.short_description = _('Duration')

    def get_update_progress(self):
        updates_array = []
        updates = self.member_problems.all()
        updates_html = ''
        for update in updates:
            localzone = timezone.localtime(update.created_at)
            updates_html += "<li><small>{}</small> <small>{}</small></li>".format(
                    localzone.strftime("%d-%m-%Y %H:%M"),
                    update.update_progress)


        return format_html("<ul>{}</ul>", format_html(updates_html))
    get_update_progress.short_description = _('Update Progress')

    def problem_duration_start(self):
        duration = self.duration_text_undone()
        start_local = timezone.localtime(self.start_at)
        start_local_text = start_local.strftime("%A, %d-%m-%Y %H:%M")
        end_local = timezone.localtime(self.end_at)
        end_local_text = end_local.strftime("%A, %d-%m-%Y %H:%M")

        return format_html("{}<br><small>D: {}<br />S: {}</small>", self.problem, duration, start_local_text)

    problem_duration_start.short_description = _('Problem')




    def get_network(self):
        return self.member.network
    get_network.short_description = _('Network')


class ProblemUpdate(models.Model):
    member_problems = ParentalKey('MemberProblems', related_name='member_problems', on_delete=models.CASCADE)
    update_progress = models.TextField(_('Update Progress'), default=None, null=True)
    created_at = models.DateTimeField(auto_now=False, auto_now_add=True)

    panels = [
            FieldRowPanel([
                FieldPanel('created_at', read_only=True),
                FieldPanel('update_progress'),
                ])
            ]

    class Meta:
        db_table = 'problem_update'


    def clean(self):
        if self.update_progress is None:
            raise ValidationError({'update_progress': _('Please provide update progress!')})


class MemberProblemsDone(MemberProblems):

    objects = MemberProblemManagerDone()

    class Meta:
        proxy = True
        verbose_name = 'Problem History'
        verbose_name_plural = 'Problems History'

    def duration_text(self):
        #delta = self.end_at - self.start_at
        return readable_timedelta_seconds(self.duration)
    duration_text.short_description = _('Duration')

    def problem_duration_start_end(self):
        duration = self.duration_text()
        start_local = timezone.localtime(self.start_at)
        start_local_text = start_local.strftime("%A, %d-%m-%Y %H:%M")
        end_local = timezone.localtime(self.end_at)
        end_local_text = end_local.strftime("%A, %d-%m-%Y %H:%M")

        return format_html("{}<br><small>D: {}<br />S: {}<br />E: {}</small>", self.problem, duration, start_local_text, end_local_text)

    problem_duration_start.short_description = _('Problem')
