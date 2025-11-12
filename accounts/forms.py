from django import forms
from wagtail.users.forms import UserEditForm, UserCreationForm
from .models import Organizations
from django.utils.translation import gettext_lazy as _


class CustomUserEditForm(UserEditForm):
    organization = forms.ModelChoiceField(
        queryset=Organizations.objects,
        required=True,
        disabled=True,
        label=_("Organization"),
    )

    class Meta(UserEditForm.Meta):
        fields = UserEditForm.Meta.fields | {"organization"}
        exclude = ["is_superuser"]


class CustomUserCreationForm(UserCreationForm):
    organization = forms.ModelChoiceField(
        queryset=Organizations.objects, required=True, label=_("Organization")
    )

    class Meta(UserCreationForm.Meta):
        fields = UserCreationForm.Meta.fields | {"organization"}
        exclude = ["is_superuser"]

