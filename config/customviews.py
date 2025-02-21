from django.db.models import ObjectDoesNotExist
from wagtail.admin.views import account
from wagtail.models import Site
from accounts.models import Organizations

# from sites_custom.models import SitesCustom


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
