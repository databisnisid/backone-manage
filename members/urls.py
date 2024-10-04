from django.urls import path
from .views import (
    get_member,
    get_member_by_network,
    get_members_all,
    get_members_user,
    get_members_org,
    get_members_by_network,
    get_members_by_network_mqtt,
)

urlpatterns = [
    path("get_all/", get_members_all, name="get_members_all"),
    path("get_member/<str:member_id>/", get_member, name="get_member"),
    path(
        "get_member_by_net/<str:member_id>/<str:network_id>/",
        get_member_by_network,
        name="get_member_by_net",
    ),
    path("get_by_user/<int:user>/", get_members_user, name="get_members_by_user"),
    path("get_by_org/<int:organization>/", get_members_org, name="get_members_by_org"),
    path(
        "get_by_net/<str:network_id>/",
        get_members_by_network,
        name="get_members_by_net",
    ),
    path(
        "get_by_net_mqtt/<str:network_id>/",
        get_members_by_network_mqtt,
        name="get_members_by_net_mqtt",
    ),
]
