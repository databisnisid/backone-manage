from django.contrib import messages
from django.http import response
from django.utils.translation import gettext_lazy as _
from wagtail.admin.views.account import LoginView as WagtailLoginView
from django.contrib.auth import REDIRECT_FIELD_NAME

from mailauth.forms import EmailLoginForm

__all__ = ("LoginView",)


class LoginView(WagtailLoginView):
    template_name = "wagtailadmin/login_email.html"
    """Authentication view for Wagtail admin."""

    def get_form_class(self):
        return EmailLoginForm

    def form_valid(self, form):
        print("Form is Valid")
        form.save()
        messages.add_message(
            self.request,
            messages.SUCCESS,
            _("We sent you an email with instructions to log into your account."),
        )
        return response.HttpResponseRedirect(self.get_success_url())

    """
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                **self.site.each_context(self.request),
                "title": _("Log in"),
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
        return context
    """
