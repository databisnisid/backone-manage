from django.urls import path
from .views import get_webfilter, get_webfilter_by_member

# Adds site header, site title, index title to the admin side.

urlpatterns = [
    path('<uuid:uuid>/', get_webfilter, name='get-webfilter'),
    path('member/<str:member>/', get_webfilter_by_member, name='get-webfilter-by-member'),
]

