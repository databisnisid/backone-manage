from django.urls import path
from .views import download_license, license_handler


urlpatterns = [
        path('download/<int:license_id>/', download_license, name='json_download'),
        path('handler/', license_handler, name='license_handler')
        ]

