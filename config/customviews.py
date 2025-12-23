import logging
from django.db.models import ObjectDoesNotExist
from django.utils.translation import gettext_lazy as _
from django.shortcuts import redirect, render
from wagtail.admin.views import account
from wagtail.models import Site
from accounts.models import Organizations
from config.settings import IS_MAILAUTH_NO_PASSWORD, IS_2FA_ENABLE

logger = logging.getLogger(__name__)


class CustomLoginView(account.LoginView):
    template_name = "wagtailadmin/login.html"

    def get(self, *args, **kwargs):

        # If user is already logged in, redirect them to the dashboard
        if self.request.user.is_authenticated and self.request.user.has_perm(
            "wagtailadmin.access_admin"
        ):
            print("LOGIN:", self.get_success_url())
            return redirect(self.get_success_url())
        elif IS_2FA_ENABLE:
            url = "/two/account/login/"
            return redirect(url)

        elif IS_MAILAUTH_NO_PASSWORD:
            url = "/custom/login/"
            return redirect(url)
            # return response.HttpResponseRedirect(url)

        return super().get(*args, **kwargs)

    def get_context_data(self, **kwargs):

        context = super().get_context_data(**kwargs)
        # print(context)

        context["show_password_reset"] = account.password_reset_enabled()

        from django.contrib.auth import get_user_model

        User = get_user_model()
        context["username_field"] = User._meta.get_field(
            User.USERNAME_FIELD
        ).verbose_name

        hostname = self.request.get_host()
        try:
            site = Site.objects.get(hostname__icontains=hostname)
            logger.info(f"Site: {site}")

            try:
                organization = Organizations.objects.get(site=site)
                context["organization"] = organization
                logger.info(f"Organization: {organization}")

            except ObjectDoesNotExist:
                logger.info("No Organization found for custom logo")

        except ObjectDoesNotExist:
            pass

        """
        if IS_MAILAUTH_NO_PASSWORD:
            self.template_name = "mailauth_admin/login.html"

            context.update(
                {
                    # **self.site.each_context(self.request),
                    # "title": _("Log in"),
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
        """

        logger.debug(f"{context}")
        return context


def custom_404(request, exception):
    context = {"exception": exception}
    return render(request, "error_pages/404.html", status=404, context=context)


def custom_500(request):
    return render(request, "error_pages/500.html", status=500)


def custom_403(request, exception):
    context = {"exception": exception}
    return render(request, "error_pages/403.html", status=403, context=context)


def custom_400(request, exception):
    context = {"exception": exception}
    return render(request, "error_pages/400.html", status=400, context=context)
