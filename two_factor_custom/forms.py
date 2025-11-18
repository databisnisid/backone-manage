from django import forms
from django.utils.translation import gettext_lazy as _
from two_factor.forms import (
    AuthenticationTokenForm,
    TOTPDeviceForm,
    DeviceValidationForm,
)

from two_factor.utils import totp_digits


class CustomAuthenticationTokenForm(AuthenticationTokenForm):
    otp_token = forms.RegexField(
        label=_("Tokem"),
        regex=r"^[0-9]*$",
        min_length=totp_digits(),
        max_length=totp_digits(),
    )


class CustomTOTPDeviceForm(TOTPDeviceForm):
    token = forms.IntegerField(
        label=_("Toket"), min_value=0, max_value=int("9" * totp_digits())
    )


class CustomDeviceValidationForm(DeviceValidationForm):
    token = forms.IntegerField(
        label=_("Tokek"), min_value=1, max_value=int("9" * totp_digits())
    )
