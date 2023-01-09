from django.db import models
from crum import get_current_user
from accounts.models import User, Organizations
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
    '''
    mqtt = models.ForeignKey(
        Mqtt,
        on_delete=models.SET_NULL,
        verbose_name=_('Mqtt'),
        null=True
    )
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
    '''

    is_done = models.BooleanField(_('Problem Solved'), default=False)

    objects = MemberProblemManagerUndone()
    unsolved = MemberProblemManagerUndone()
    solved = MemberProblemManagerDone()
    alls = models.Manager()

    start_at = models.DateTimeField(auto_now=False, auto_now_add=True)
    end_at = models.DateTimeField(auto_now=True, auto_now_add=False)

    class Meta:
        db_table = 'member_problem'
        verbose_name = _('Member Problem')
        verbose_name_plural = _('Member Problems')

    def __str__(self):
        return '{}'.format(self.member)

