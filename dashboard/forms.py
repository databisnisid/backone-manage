# from django import forms
# from accounts.models import User
# from django.contrib.auth import get_user_model

# from wagtail import forms
# from wagtail.admin.forms.models import WagtailAdminModelForm


# User = get_user_model()


# class ReadOnlyProfileForm(forms.ModelForm):
"""
class ReadOnlyProfileForm(WagtailAdminModelForm):
    class Meta:
        model = User
        fields = ["first_name", "last_name", "email"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set fields to disabled so they cannot be edited
        self.fields["first_name"].label = "First Name"
        # self.fields["first_name"].disabled = True
        self.fields["first_name"].read_only = True
        self.fields["last_name"].label = "Last Name"
        # self.fields["last_name"].disabled = True
        self.fields["first_name"].read_only = True
        self.fields["email"].label = "Email Address"
        # self.fields["email"].disabled = True
        self.fields["first_name"].read_only = True
"""
