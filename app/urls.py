from django.urls import path

from . import views

urlpatterns = [
    path("", views.me, name="app_me"),
    path("me/", views.me, name="app_me"),
    path("members/", views.members, name="app_members"),
    path("members/<str:member_id>/telemetry/", views.member_telemetry, name="app_member_telemetry"),
    path("networks/", views.networks, name="app_networks"),
    path("networks/create/", views.network_create, name="app_network_create"),
    path("networks/<str:network_id>/", views.network_detail, name="app_network_detail"),
    path("networks/<str:network_id>/update/", views.network_update, name="app_network_update"),
    path("networks/<str:network_id>/routes/", views.network_routes_list_create, name="app_network_routes"),
    path("networks/<str:network_id>/routes/<path:ip_network>/", views.network_route_detail, name="app_network_route_detail"),
    path("ip-loc/", views.ip_loc, name="app_ip_loc"),
    path("summary/", views.summary, name="app_summary"),
    path("problems/", views.problems, name="app_problems"),
]
