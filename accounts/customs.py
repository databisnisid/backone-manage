from django.contrib.admin import SimpleListFilter
from django.db.models import ObjectDoesNotExist
from django.utils.translation import gettext_lazy as _

from accounts.models import GroupOrganizations, Organizations


class GroupOrganizationFilter(SimpleListFilter):
    title = _("Organization")
    parameter_name = "organization"

    def lookups(self, request, model_admin):
        member_org_list = []
        try:
            g_org = GroupOrganizations.objects.get(main_org=request.user.organization)
            member_orgs = g_org.member_org.all()
            for c in member_orgs:
                member_org_dict = {
                    "id": c.id,
                    "display_name": c.name,
                }
                member_org_list.append(member_org_dict)

            return [(c["id"], c["display_name"]) for c in member_org_list]

        except ObjectDoesNotExist:
            return None

    def queryset(self, request, queryset):
        if self.value():
            try:
                member_org_id = self.value()
            except ValueError:
                return queryset.none()
            else:
                org = Organizations.objects.get(id=member_org_id)
                return queryset.filter(organization=org)
