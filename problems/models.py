from django.core.validators import ValidationError
from django.db import models
from members.models import Members
from monitor.models import MonitorRules
from django.utils.translation import gettext as _
from django.utils import timezone
from django.utils.html import format_html
from config.utils import readable_timedelta_seconds
from modelcluster.models import ClusterableModel
from modelcluster.fields import ParentalKey


DURATION_RED_ALERT = 3600


class MemberProblemManagerUndone(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(is_done=False).exclude(member=None)


class MemberProblemManagerDone(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(is_done=True).exclude(member=None)


class MemberProblems(ClusterableModel):
    member = models.ForeignKey(
        Members, on_delete=models.SET_NULL, verbose_name=_("Member"), null=True
    )
    problem = models.ForeignKey(
        MonitorRules, on_delete=models.RESTRICT, verbose_name=_("Problem")
    )

    is_done = models.BooleanField(_("Problem Solved"), default=False)
    duration = models.IntegerField(_("Duration"), default=0)

    unsolved = MemberProblemManagerUndone()
    solved = MemberProblemManagerDone()
    alls = models.Manager()
    objects = models.Manager()

    start_at = models.DateTimeField(auto_now=False, auto_now_add=True)
    end_at = models.DateTimeField(auto_now=True, auto_now_add=False)

    class Meta:
        db_table = "member_problem"
        verbose_name = _("Member Problem")
        verbose_name_plural = _("Member Problems")

    def __str__(self):
        return "{}".format(self.member)

    def save(self):
        if self.is_done:
            delta = timezone.now() - timezone.localtime(self.start_at)
            self.duration = delta.total_seconds()

        return super(MemberProblems, self).save()

    def duration_text_undone(self):
        delta = timezone.now() - timezone.localtime(self.start_at)

        color = "black"
        # if delta.seconds > DURATION_RED_ALERT:
        if delta.total_seconds() > DURATION_RED_ALERT:
            color = "red"

        # print(readable_timedelta_seconds(delta.total_seconds()), delta.seconds)
        duration_html = format_html(
            "<span style='style: {}'>{}</span>",
            color,
            readable_timedelta_seconds(delta.total_seconds()),
        )
        return duration_html

    duration_text_undone.short_description = _("Duration")

    def get_update_progress(self):
        updates_array = []
        updates = self.member_problems.all()
        updates_html = ""
        for update in updates:
            localzone = timezone.localtime(update.created_at)
            updates_html += "<small>{}</small> <small>{}</small><br />".format(
                localzone.strftime("%d-%m-%Y %H:%M"), update.update_progress
            )

        return format_html(updates_html)

    get_update_progress.short_description = _("Update Progress")

    def member_name_with_update_progress(self):
        text = format_html("{}<br />{}", self.member, self.get_update_progress())
        return text

    member_name_with_update_progress.short_description = _("Member Name")
    member_name_with_update_progress.admin_order_field = "member__name"

    def problem_duration_start(self):
        duration = self.duration_text_undone()
        start_local = timezone.localtime(self.start_at)
        start_local_text = start_local.strftime("%A, %d-%m-%Y %H:%M")
        end_local = timezone.localtime(self.end_at)
        end_local_text = end_local.strftime("%A, %d-%m-%Y %H:%M")

        return format_html(
            "{}<br><small>D: {}<br />S: {}</small>",
            self.problem,
            duration,
            start_local_text,
        )

    problem_duration_start.short_description = _("Problem")
    problem_duration_start.admin_order_field = "start_at"

    def get_network(self):
        return self.member.network

    get_network.short_description = _("Network")

    def get_parameters(self):
        return self.member.model_release()

    get_parameters.short_description = _("Parameters")
    get_parameters.admin_order_field = "start_at"


class ProblemUpdate(models.Model):
    member_problems = ParentalKey(
        "MemberProblems", related_name="member_problems", on_delete=models.CASCADE
    )
    update_progress = models.TextField(_("Update Progress"), default=None, null=True)
    created_at = models.DateTimeField(auto_now=False, auto_now_add=True)

    class Meta:
        db_table = "problem_update"

    def clean(self):
        if self.update_progress is None:
            raise ValidationError(
                {"update_progress": _("Please provide update progress!")}
            )


class MemberProblemsDone(MemberProblems):

    objects = MemberProblemManagerDone()

    class Meta:
        proxy = True
        verbose_name = "Problem History"
        verbose_name_plural = "Problems History"

    def duration_text(self):
        # delta = self.end_at - self.start_at
        return readable_timedelta_seconds(self.duration)

    duration_text.short_description = _("Duration")

    def problem_duration_start_end(self):
        duration = self.duration_text()
        start_local = timezone.localtime(self.start_at)
        start_local_text = start_local.strftime("%A, %d-%m-%Y %H:%M")
        end_local = timezone.localtime(self.end_at)
        end_local_text = end_local.strftime("%A, %d-%m-%Y %H:%M")

        return format_html(
            "{}<br><small>D: {}<br />S: {}<br />E: {}</small>",
            self.problem,
            duration,
            start_local_text,
            end_local_text,
        )

    problem_duration_start_end.short_description = _("Problem")
    problem_duration_start_end.admin_order_field = "duration"
