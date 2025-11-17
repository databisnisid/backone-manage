from django.conf import settings
from django.db.models import ObjectDoesNotExist
from django.contrib.auth import REDIRECT_FIELD_NAME, authenticate, login
from django.contrib.auth.views import LoginView as DjangoLoginView
from django.core.exceptions import PermissionDenied
from django.http import response
from django.shortcuts import resolve_url
from django.utils.decorators import method_decorator
from django.views import generic
from django.views.decorators.cache import never_cache
from wagtail.models import Site
from accounts.models import Organizations
from mailauth import forms

__all__ = (
    "LoginView",
    "LoginTokenView",
)


class LoginView(DjangoLoginView):
    """
    Send a login code to the user.

    It doesn't authenticate a user but it is the entry point for the login
    process (login URL).
    """

    form_class = forms.EmailLoginForm
    success_url = getattr(settings, "LOGIN_REQUESTED_URL", "mailauth:login-success")
    template_name = "registration/login.html"
    redirect_field_name = REDIRECT_FIELD_NAME

    def form_valid(self, form):
        form.save()
        return response.HttpResponseRedirect(self.get_success_url())

    def get_success_url(self):
        return resolve_url(self.success_url)

    def get_initial(self):
        return {
            self.redirect_field_name: self.request.GET.get(self.redirect_field_name),
            **super().get_initial(),
        }


INTERNAL_LOGIN_URL_TOKEN = "login-token"  # noqa: S105


class LoginTokenView(DjangoLoginView):
    """Authenticate a user via an access token."""

    redirect_field_name = REDIRECT_FIELD_NAME

    @method_decorator(never_cache)
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        print(self)
        print(request)
        print(args)
        print(kwargs)

        token = kwargs["token"]

        user = authenticate(request, token=token)
        if user is None:
            raise PermissionDenied
        login(self.request, user=user)
        # Remove token from the HTTP Referer header
        self.request.path.replace(token, INTERNAL_LOGIN_URL_TOKEN)

        return response.HttpResponseRedirect(self.get_success_url())

    def post(self, request, *args, **kwargs):
        return self.http_method_not_allowed(request, *args, **kwargs)


class LoginRequestedView(generic.TemplateView):
    template_name = "registration/login_requested.html"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # print(self.template_name)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        print(context)

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
