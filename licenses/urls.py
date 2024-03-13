from django.urls import path
from .views import json_download


urlpatterns = [
        path('json/<int:license_id>/', json_download, name='json_download')
        ]

