from two_factor.views.profile import ProfileView as TFProfileView
from two_factor.utils import default_device
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import never_cache
from django.shortcuts import redirect
from django.conf import settings


@method_decorator([never_cache, login_required], name="dispatch")
class CustomProfileView(TFProfileView):
    """
    View used by users for managing two-factor configuration.

    This view shows whether two-factor has been configured for the user's
    account. If two-factor is enabled, it also lists the primary verification
    method and backup verification methods.
    """

    template_name = "two_factor/profile/profile.html"

    def get_context_data(self, **kwargs):
        user = self.request.user

        try:
            backup_tokens = user.staticdevice_set.all()[0].token_set.count()

        except Exception:
            backup_tokens = 0

        context = super().get_context_data(**kwargs)
        context.update(
            {
                "default_device": default_device(user),
                "default_device_type": default_device(user).__class__.__name__,
                "backup_tokens": backup_tokens,
            }
        )

        if apps.is_installed("two_factor.plugins.phonenumber"):
            from two_factor.plugins.phonenumber.utils import (
                backup_phones,
                get_available_phone_methods,
            )

            context.update(
                {
                    "backup_phones": backup_phones(self.request.user),
                    "available_phone_methods": get_available_phone_methods(),
                }
            )

        context["page_timeout"] = settings.IS_2FA_PROFILE_TIMEOUT

        return context

        # return super().get(request, *args, **kwargs)
