from django.urls import path

from . import views

urlpatterns = [
    path("", views.me, name="app_me"),
    path("me/", views.me, name="app_me"),
    path("members/", views.members, name="app_members"),
    path("members/<str:member_id>/telemetry/", views.member_telemetry, name="app_member_telemetry"),
    path("networks/", views.networks, name="app_networks"),
    path("summary/", views.summary, name="app_summary"),
    path("problems/", views.problems, name="app_problems"),
]