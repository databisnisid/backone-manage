import django_otp
import warnings
from django.shortcuts import redirect, resolve_url
from django.contrib.auth import REDIRECT_FIELD_NAME, login
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.cache import never_cache
from django.views.decorators.debug import sensitive_post_parameters
from django.conf import settings
from django.utils.decorators import method_decorator
from two_factor.views import LoginView as TFLoginView, SetupView as TFSetupView
from wagtail.admin.forms.auth import LoginForm as AuthenticationForm
from .forms import (
    CustomAuthenticationTokenForm,
    CustomTOTPDeviceForm,
    CustomDeviceValidationForm,
)
from .mixins import CustomOTPRequiredMixin
from two_factor.forms import AuthenticationTokenForm, BackupTokenForm
from two_factor import signals
from two_factor.views.utils import (
    get_remember_device_cookie,
    validate_remember_device_cookie,
)
from django.db.models import ObjectDoesNotExist
from wagtail.models import Site
from accounts.models import Organizations

try:
    from django.contrib.auth.decorators import login_not_required
except ImportError:
    # For Django < 5.1, copy the current Django implementation
    def login_not_required(view_func):
        """
        Decorator for views that allows access to unauthenticated requests.
        """
        view_func.login_required = False
        return view_func


REMEMBER_COOKIE_PREFIX = getattr(
    settings, "TWO_FACTOR_REMEMBER_COOKIE_PREFIX", "remember-cookie_"
)


@method_decorator(
    [login_not_required, sensitive_post_parameters(), csrf_protect, never_cache],
    name="dispatch",
)
class CustomTFLoginView(TFLoginView):
    AUTH_STEP = "auth"
    TOKEN_STEP = "token"
    BACKUP_STEP = "backup"
    FIRST_STEP = AUTH_STEP

    template_name = "two_factor/core/login.html"

    form_list = (
        (AUTH_STEP, AuthenticationForm),
        (TOKEN_STEP, CustomAuthenticationTokenForm),
        # (TOKEN_STEP, AuthenticationTokenForm),
        (BACKUP_STEP, BackupTokenForm),
    )

    """
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        print("I am used!")
    """

    def get(self, request, *args, **kwargs):
        if not settings.IS_2FA_ENABLE:
            return redirect("/")

        return super().get(request, *args, **kwargs)

    def get_context_data(self, form, **kwargs):
        """
        Adds user's default and backup OTP devices to the context.
        """
        context = super().get_context_data(form, **kwargs)
        if self.steps.current == self.TOKEN_STEP:
            device = self.get_device()
            context["device"] = device
            context["other_devices"] = self.get_other_devices(device)
            context["backup_tokens"] = (
                self.get_user()
                .staticdevice_set.all()
                .values("token_set__token")
                .count()
            )

        if getattr(settings, "LOGOUT_REDIRECT_URL", None):
            context["cancel_url"] = resolve_url(settings.LOGOUT_REDIRECT_URL)
        elif getattr(settings, "LOGOUT_URL", None):
            warnings.warn(
                "LOGOUT_URL has been replaced by LOGOUT_REDIRECT_URL, please "
                "review the URL and update your settings.",
                DeprecationWarning,
            )
            context["cancel_url"] = resolve_url(settings.LOGOUT_URL)

        print("CONTEXT", context)
        """ For Custom Logo in Login """
        """
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
        """
        return context

    def done(self, form_list, **kwargs):
        """
        Login the user and redirect to the desired page.
        """

        # Check if remember cookie should be set after login
        current_step_data = self.storage.get_step_data(self.steps.current)
        remember = bool(
            current_step_data and current_step_data.get("token-remember") == "on"
        )

        login(self.request, self.get_user())

        redirect_to = self.get_success_url()

        device = getattr(self.get_user(), "otp_device", None)
        response = redirect(redirect_to)

        if device:
            signals.user_verified.send(
                sender=__name__,
                request=self.request,
                user=self.get_user(),
                device=device,
            )

            # Set a remember cookie if activated

            if getattr(settings, "TWO_FACTOR_REMEMBER_COOKIE_AGE", None) and remember:
                # choose a unique cookie key to remember devices for multiple users in the same browser
                cookie_key = REMEMBER_COOKIE_PREFIX + str(uuid4())
                cookie_value = get_remember_device_cookie(
                    user=self.get_user(), otp_device_id=device.persistent_id
                )
                response.set_cookie(
                    cookie_key,
                    cookie_value,
                    max_age=settings.TWO_FACTOR_REMEMBER_COOKIE_AGE,
                    domain=getattr(settings, "TWO_FACTOR_REMEMBER_COOKIE_DOMAIN", None),
                    path=getattr(settings, "TWO_FACTOR_REMEMBER_COOKIE_PATH", "/"),
                    secure=getattr(
                        settings, "TWO_FACTOR_REMEMBER_COOKIE_SECURE", False
                    ),
                    httponly=getattr(
                        settings, "TWO_FACTOR_REMEMBER_COOKIE_HTTPONLY", True
                    ),
                    samesite=getattr(
                        settings, "TWO_FACTOR_REMEMBER_COOKIE_SAMESITE", "Lax"
                    ),
                )
            return response

        # If the user does not have a device.
        elif CustomOTPRequiredMixin.is_otp_view(self.request.GET.get("next")):
            # elif OTPRequiredMixin.is_otp_view(self.request.GET.get("next")):
            if self.request.GET.get("next"):
                self.request.session["next"] = self.get_success_url()
            return redirect("two_factor:setup")

        return response


@method_decorator([never_cache, login_required], name="dispatch")
class CustomSetupView(TFSetupView):
    test_me = True

    def done(self, form_list, **kwargs):
        """
        Finish the wizard. Save all forms and redirect.
        """
        # Remove secret key used for QR code generation
        try:
            del self.request.session[self.session_key_name]
        except KeyError:
            pass

        method = self.get_method()
        # TOTPDeviceForm
        if method.code == "generator":
            # form = [form for form in form_list if isinstance(form, TOTPDeviceForm)][0]
            form = [
                form for form in form_list if isinstance(form, CustomTOTPDeviceForm)
            ][0]
            device = form.save()

        # PhoneNumberForm / YubiKeyDeviceForm / EmailForm / WebauthnDeviceValidationForm
        elif method.code in ("call", "sms", "yubikey", "email", "webauthn"):
            device = self.get_device()
            device.confirmed = True
            device.save()

        django_otp.login(self.request, device)
        return redirect(self.get_success_url())

        form_class = self.get_form_list()[step]
