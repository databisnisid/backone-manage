from django.db import models
from django.utils.translation import gettext_lazy as _


class HS_Users(models.Model):
    name = models.CharField(_('Name'), max_length=100)

    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()
    deleted_at = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'users'

