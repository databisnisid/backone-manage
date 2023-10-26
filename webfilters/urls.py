from django.urls import path
from .views import get_webfilter

# Adds site header, site title, index title to the admin side.

urlpatterns = [
    path('<uuid:uuid>/', get_webfilter, name='get-webfilter'),
]

