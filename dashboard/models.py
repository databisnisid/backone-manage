from django.db import models
from networks.models import Networks, NetworkRoutes
from members.models import Members
from django.utils.translation import gettext as _
from accounts.models import User, Organizations
#from config.utils import get_user
from django.core.exceptions import ObjectDoesNotExist
from crum import get_current_user


class Statistics(models.Model):
    networks = models.IntegerField()
    members = models.IntegerField()
    routes = models.IntegerField()
    members_online = models.IntegerField()

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name=_('Owner'),
    )
    #organization = models.ForeignKey(
    #    Organizations,
    #    on_delete=models.SET_NULL,
    #    verbose_name=_('Organization'),
    #    null=True
    #)

    created_at = models.DateTimeField(auto_now=False, auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True, auto_now_add=False)

    class Meta:
        db_table = 'statistics'
        verbose_name = _('statistic')
        verbose_name_plural = _('statistics')

    def save(self):
        #try:
        #    self.user
        #except ObjectDoesNotExist:
        #    self.user = get_user()
        #    #self.user = get_current_user()
        #    print(self.user)
        #if self.user is None:
        self.user = get_current_user()
        if self.user.organization.is_no_org:
            self.networks = Networks.objects.filter(user=self.user).count()
            self.members = Members.objects.filter(user=self.user).distinct('member_id').count()
            self.routes = NetworkRoutes.objects.filter(user=self.user).count()
        else:
            self.networks = Networks.objects.filter(organization=self.user.organization).count()
            self.members = Members.objects.filter(organization=self.user.organization).distinct('member_id').count()
            self.routes = NetworkRoutes.objects.filter(organization=self.user.organization).count()

        members = Members.objects.filter(user=self.user)

        for member in members:
            pass
        
        return super(Statistics, self).save()

