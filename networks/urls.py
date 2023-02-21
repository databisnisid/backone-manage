from django.conf.urls import include
from django.urls import path

urlpatterns = [
    path('qr_code/', include('qr_code.urls', namespace="qr_code")),
]

