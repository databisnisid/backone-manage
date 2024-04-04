from django.conf.urls import include
from django.urls import path
from .views import networks_list_json, qr_code, network_ping_stats


urlpatterns = [
    #path('qr_code/', include('qr_code.urls', namespace="qr_code")),
    path('list/', networks_list_json, name='networks-list'),
    path('qr_code/<str:network_id>/', qr_code, name='qr-code'),
    path('pingstat/<str:network_id>/', network_ping_stats, name='network-ping-stats'),
]

