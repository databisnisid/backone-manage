from django import forms
from wagtail.users.forms import UserEditForm, UserCreationForm
from django.contrib.auth.models import Group
from .models import Organizations
from django.utils.translation import gettext_lazy as _
from crum import get_current_user


class CustomUserEditForm(UserEditForm):
    organization = forms.ModelChoiceField(
        queryset=Organizations.objects,
        required=True,
        disabled=True,
        label=_("Organization"),
    )

    def __init__(self, *args, **kwargs):
        editing_self = kwargs.pop("editing_self", False)
        super().__init__(*args, **kwargs)
        current_user = get_current_user()

        if editing_self or not current_user.is_superuser:
            del self.fields["is_active"]
            del self.fields["is_superuser"]

    class Meta(UserEditForm.Meta):
        fields = UserEditForm.Meta.fields | {"organization"}
        # exclude = ["is_superuser"]


class CustomUserCreationForm(UserCreationForm):
    organization = forms.ModelChoiceField(
        queryset=Organizations.objects, required=True, label=_("Organization")
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        current_user = get_current_user()

        if not current_user.is_superuser:
            del self.fields["is_superuser"]

    class Meta(UserCreationForm.Meta):
        fields = UserCreationForm.Meta.fields | {"organization"}
        # exclude = ["is_superuser"]

