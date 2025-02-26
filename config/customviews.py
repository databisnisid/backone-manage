from django.db.models import ObjectDoesNotExist
from django.utils.translation import gettext_lazy as _
from wagtail.admin.views import account, home
from wagtail.models import Site
from wagtail.admin.site_summary import SiteSummaryPanel
from wagtail.admin.forms.search import SearchForm
from accounts.models import Organizations


class CustomHomeView(home.HomeView):
    template_name = "wagtailadmin/home.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        panels = self.get_panels()
        site_summary = SiteSummaryPanel(self.request)
        site_details = self.get_site_details()

        context["media"] = self.get_media([*panels, site_summary])
        context["panels"] = sorted(panels, key=lambda p: p.order)
        context["site_summary"] = site_summary
        context["upgrade_notification"] = home.UpgradeNotificationPanel()
        context["search_form"] = SearchForm(placeholder=_("Search all pages…"))
        context["user"] = self.request.user

        try:
            site = Site.objects.get(hostname__icontains=context["site_name"])
            # print(site)

            try:
                organization = Organizations.objects.get(site=site)
                context["organization"] = organization

            except ObjectDoesNotExist:
                pass
                # print("NO Organization")

        except ObjectDoesNotExist:
            pass

        return {**context, **site_details}


class CustomLoginView(account.LoginView):
    template_name = "wagtailadmin/login.html"

    def get_context_data(self, **kwargs):

        context = super().get_context_data(**kwargs)

        context["show_password_reset"] = account.password_reset_enabled()

        from django.contrib.auth import get_user_model

        User = get_user_model()
        context["username_field"] = User._meta.get_field(
            User.USERNAME_FIELD
        ).verbose_name

        # print(context["site_name"])
        # print(context["site"])

        try:
            site = Site.objects.get(hostname__icontains=context["site_name"])
            # print(site)

            try:
                organization = Organizations.objects.get(site=site)
                context["organization"] = organization

            except ObjectDoesNotExist:
                pass
                # print("NO Organization")

        except ObjectDoesNotExist:
            pass

        return context
