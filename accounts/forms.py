from django import forms
from django.db.models import query
from wagtail.users.forms import UserEditForm, UserCreationForm
from django.contrib.auth.models import Group
from .models import Organizations, User
from django.utils.translation import gettext_lazy as _
from crum import get_current_user

# Avatar
from wagtail.users.models import UserProfile


class CustomUserEditForm(UserEditForm):
    organization = forms.ModelChoiceField(
        queryset=Organizations.objects,
        required=True,
        disabled=True,
        label=_("Organization"),
    )

    username = forms.CharField(
        disabled=True,
        label=_("Username"),
    )
    # Avatar
    avatar = forms.ImageField(required=False, label="Profile Picture")

    def __init__(self, *args, **kwargs):
        editing_self = kwargs.pop("editing_self", False)
        super().__init__(*args, **kwargs)
        current_user = get_current_user()

        self.profile = UserProfile.get_for_user(self.instance)

        if editing_self or not current_user.is_superuser:
            del self.fields["is_active"]
            del self.fields["is_superuser"]

        # if "groups" in self.fields:
        #    del self.fields["groups"]

        if self.profile:
            self.fields["avatar"].initial = self.profile.avatar

    def save(self, commit=True):
        # Save the User object first
        user = super().save(commit=commit)

        # Update the associated UserProfile
        if commit:
            profile = UserProfile.get_for_user(user=self.instance)
            avatar_data = self.cleaned_data.get("avatar")
            profile.avatar = avatar_data if avatar_data else None

            profile.save()

        return user

    class Meta(UserEditForm.Meta):
        fields = UserEditForm.Meta.fields | {
            "avatar",
            "organization",
            "is_member_filter",
            "is_remote_ssh",
            "is_remote_web",
        }
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
        fields = UserCreationForm.Meta.fields | {
            "organization",
            "is_member_filter",
            "is_remote_ssh",
            "is_remote_web",
        }
        # exclude = ["is_superuser"]
