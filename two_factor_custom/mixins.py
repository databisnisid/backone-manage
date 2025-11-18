from two_factor.views.mixins import OTPRequiredMixin as TFOTPRequiredMixin
from two_factor.utils import default_device
from django.core.exceptions import PermissionDenied
from django.template.response import TemplateResponse
from django.contrib.auth.views import redirect_to_login


class CustomOTPRequiredMixin(TFOTPRequiredMixin):

    def dispatch(self, request, *args, **kwargs):
        if (
            not request.user
            or not request.user.is_authenticated
            or (not request.user.is_verified() and default_device(request.user))
        ):
            # If the user has not authenticated raise or redirect to the login
            # page. Also if the user just enabled two-factor authentication and
            # has not yet logged in since should also have the same result. If
            # the user receives a 'you need to enable TFA' by now, he gets
            # confuses as TFA has just been enabled. So we either raise or
            # redirect to the login page.
            if self.raise_anonymous:
                raise PermissionDenied()
            else:
                return redirect_to_login(request.get_full_path(), self.get_login_url())

        if not request.user.is_verified():
            if self.raise_unverified:
                raise PermissionDenied()
            elif self.get_verification_url():
                return redirect_to_login(
                    request.get_full_path(), self.get_verification_url()
                )
            else:
                return TemplateResponse(
                    request=request,
                    template="two_factor/core/otp_required.html",
                    status=403,
                )
        return super().dispatch(request, *args, **kwargs)
