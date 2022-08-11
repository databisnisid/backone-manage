from .backend import Zerotier
from .models import Controllers, UserControllers
from networks.models import Networks, Members

from django.urls import reverse
from wagtail.contrib.modeladmin.options import (ModelAdmin, modeladmin_register)
from wagtail.contrib.modeladmin.helpers import (PageAdminURLHelper, PageButtonHelper)
# MyPage model import not included but will be needed


def import_networks(self, request, queryset):
        for obj in queryset:
    zt = Zerotier

import_networks.short_description = 'Check Firewall'
