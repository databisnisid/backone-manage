from two_factor.views.profile import ProfileView as TFProfileView
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import never_cache
from django.shortcuts import redirect


@method_decorator([never_cache, login_required], name="dispatch")
class CustomProfileView(TFProfileView):

    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)
