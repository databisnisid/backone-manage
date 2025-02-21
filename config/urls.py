from django.conf import settings
from django.urls import include, path
from django.contrib import admin
from networks import views
from wagtail.admin import urls as wagtailadmin_urls
from wagtail import urls as wagtail_urls
from wagtail.documents import urls as wagtaildocs_urls
from .customviews import CustomLoginView

# from members.views import get_members_all, get_members_user, get_members_org

# from search import views as search_views

urlpatterns = [
    path("django-admin/", admin.site.urls),
    # path('networks/qr_code/<str:network_id>/', views.qr_code),
    path("networks/", include("networks.urls")),
    path("api/networks/", include("networks.urls")),
    path("api/members/", include("members.urls")),
    # path('api/members/get_all/', get_members_all, name='get_members_all'),
    # path('api/members/get_by_user/<int:user>/', get_members_user, name='get_members_by_user'),
    # path('api/members/get_by_org/<int:organization>/', get_members_org, name='get_members_by_org'),
    path("api/webfilters/", include("webfilters.urls")),
    path("api/licenses/", include("licenses.urls")),
    path("login/", CustomLoginView.as_view(), name="custom_login_view"),
    path("", include(wagtailadmin_urls)),
    # path("login/", CustomLoginView.as_view(), name="custom_login_view"),
    path("documents/", include(wagtaildocs_urls)),
    # path("search/", search_views.search, name="search"),
]


if settings.DEBUG:
    from django.conf.urls.static import static
    from django.contrib.staticfiles.urls import staticfiles_urlpatterns

    # Serve static and media files from development server
    urlpatterns += staticfiles_urlpatterns()
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

urlpatterns = urlpatterns + [
    # For anything not caught by a more specific rule above, hand over to
    # Wagtail's page serving mechanism. This should be the last pattern in
    # the list:
    path("", include(wagtail_urls)),
    # Alternatively, if you want Wagtail pages to be served from a subpath
    # of your site, rather than the site root:
    #    path("pages/", include(wagtail_urls)),
]
