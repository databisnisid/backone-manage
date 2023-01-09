from django.db import models
from mqtt.models import Mqtt
from members.models import Members
from django.utils.translation import gettext as _


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


class MonitorRules(models.Model):
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

    created_at = models.DateTimeField(auto_now=False, auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True, auto_now_add=False)

    class Meta:
        db_table = 'monitor_rules'
        verbose_name = _('Monitor Rule')
        verbose_name_plural = _('Monitor Rules')

    def __str__(self):
        return '{}'.format(self.name)


class MemberProblemManagerUndone(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(
            is_done=False
        ).exclude(member=None)


class MemberProblems(models.Model):
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
    mqtt = models.ForeignKey(
        Mqtt,
        on_delete=models.SET_NULL,
        verbose_name=_('Mqtt'),
        null=True
    )

    is_done = models.BooleanField(_('Problem Solved'), default=False)

    objects = MemberProblemManagerUndone()
    alls = models.Manager()

    start_at = models.DateTimeField(auto_now=False, auto_now_add=True)
    end_at = models.DateTimeField(auto_now=True, auto_now_add=False)

    class Meta:
        db_table = 'member_problem'
        verbose_name = _('Member Problem')
        verbose_name_plural = _('Member Problems')

    def __str__(self):
        return '{}'.format(self.name)
