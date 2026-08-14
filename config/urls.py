from django.contrib import admin
from django.urls import (
    include,
    path,
)

from dashboard.views import landing_page

from .views import health_check


urlpatterns = [
    path(
        "",
        landing_page,
        name="landing",
    ),
    path(
        "health/",
        health_check,
        name="health_check",
    ),
    path(
        "admin/",
        admin.site.urls,
    ),
    path(
        "dashboard/",
        include("dashboard.urls"),
    ),
    path(
        "notifications/",
        include("notifications.urls"),
    ),
    path(
        "accounts/",
        include("accounts.urls"),
    ),
    path(
        "flights/",
        include("flights.urls"),
    ),
    path(
        "airlines/",
        include("airlines.urls"),
    ),
    path(
        "fleet/",
        include("fleet.urls"),
    ),
    path(
        "operations/",
        include("operations.urls"),
    ),
    path(
        "audit/",
        include("audit.urls"),
    ),
    path(
        "security/",
        include("security.urls"),
    ),
    path(
        "passenger-service/",
        include(
            "passenger_service.urls"
        ),
    ),
]