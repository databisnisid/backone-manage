from django.contrib.auth import REDIRECT_FIELD_NAME
from django.urls import reverse
from django.shortcuts import redirect
from django.db.models import ObjectDoesNotExist
from django.utils.translation import gettext_lazy as _
from accounts.models import Organizations
from wagtail.models import Site
from config.settings import IS_MAILAUTH_NO_PASSWORD
from mailauth.views import LoginView


class AdminLoginView(LoginView):
    template_name = "mailauth_admin/login.html"
    site = None

    def get(self, request, *args, **kwargs):

        if not IS_MAILAUTH_NO_PASSWORD:
            # base_url = request.site.root_url
            # print("Base Url", base_url)
            return redirect("/")

        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                **self.site.each_context(self.request),
                "title": _("Log in"),
                "app_path": self.request.get_full_path(),
                "username": self.request.user.get_username(),
            }
        )
        if (
            REDIRECT_FIELD_NAME not in self.request.GET
            and REDIRECT_FIELD_NAME not in self.request.POST
        ):
            context[REDIRECT_FIELD_NAME] = reverse(
                "admin:index", current_app=self.site.name
            )

        """ To be compatible with Wagtail Login for custom Logo"""
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
