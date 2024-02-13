from django.urls import path
from .views import get_webfilter_by_member, get_webfilter_by_network

# Adds site header, site title, index title to the admin side.

urlpatterns = [
#    path('<uuid:uuid>/', get_webfilter, name='get-webfilter'),
#    path('black/<uuid:uuid>/', get_webfilter, name='get-webfilter-black'),
#    path('white/<uuid:uuid>/', get_webfilter, name='get-webfilter-white'),
#    path('block/<uuid:uuid>/', get_webfilter, name='get-webfilter-block'),
    path('network/<str:network_id>/', get_webfilter_by_network, name='net-webfilter'),
    path('member/<str:member>/', get_webfilter_by_member, name='get-webfilter-by-member'),
]

