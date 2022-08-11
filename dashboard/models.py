from django.db import models
from networks.models import Networks, NetworkRoutes, Members, MemberPeers
from django.utils.translation import gettext as _
from django.contrib.auth.models import User
from config.utils import to_dictionary, get_user
from django.core.exceptions import ObjectDoesNotExist


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

    created_at = models.DateTimeField(auto_now=False, auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True, auto_now_add=False)

    class Meta:
        db_table = 'statistics'
        verbose_name = _('statistic')
        verbose_name_plural = _('statistics')

    def save(self):
        try:
            self.user
        except ObjectDoesNotExist:
            self.user = get_user()

        self.networks = Networks.objects.filter(user=self.user).count()
        self.members = Members.objects.filter(user=self.user).distinct('member_id').count()
        self.routes = NetworkRoutes.objects.filter(user=self.user).count()

        members = Members.objects.filter(user=self.user)

        for member in members:
            pass
        
        return super(Statistics, self).save()

