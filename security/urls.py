from django.urls import path

from .views import (
    security_report_assign,
    security_report_change_status,
    security_report_create,
    security_report_detail,
    security_report_list,
)


app_name = "security"


urlpatterns = [
    path(
        "",
        security_report_list,
        name="list",
    ),

    path(
        "create/",
        security_report_create,
        name="create",
    ),

    path(
        "<int:id>/",
        security_report_detail,
        name="detail",
    ),

    path(
        "<int:id>/assign/",
        security_report_assign,
        name="assign",
    ),

    path(
        "<int:id>/status/",
        security_report_change_status,
        name="change_status",
    ),
]