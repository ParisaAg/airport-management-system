from django.contrib.auth.decorators import (
    login_required,
)
from django.shortcuts import render

from flights.models import Flight
from notifications.models import Notification
from operations.models import GroundOperation

from .services import (
    DashboardService,
    LandingPageService,
)


ADMIN = "ADMIN"
AIRPORT_MANAGER = "AIRPORT_MANAGER"
AIRLINE_OPERATOR = "AIRLINE_OPERATOR"
GROUND_STAFF = "GROUND_STAFF"
SECURITY_OFFICER = "SECURITY_OFFICER"
PASSENGER_SERVICE = "PASSENGER_SERVICE"


@login_required
def dashboard_view(request):
    user = request.user
    role = user.role

    is_admin = (
        user.is_superuser
        or role == ADMIN
    )

    can_view_global_operations = (
        is_admin
        or role
        in {
            AIRPORT_MANAGER,
            GROUND_STAFF,
        }
    )

    can_view_security = (
        is_admin
        or role
        in {
            AIRPORT_MANAGER,
            SECURITY_OFFICER,
        }
    )

    can_view_passenger = (
        is_admin
        or role
        in {
            AIRPORT_MANAGER,
            PASSENGER_SERVICE,
        }
    )

    can_view_global_flights = (
        is_admin
        or role == AIRPORT_MANAGER
    )

    airline_stats = None

    visible_flights = Flight.objects.none()
    visible_operations = (
        GroundOperation.objects.none()
    )

    if (
        role == AIRLINE_OPERATOR
        and user.airline_id
    ):
        visible_flights = (
            Flight.objects.filter(
                airline_id=user.airline_id
            )
        )

        airline_stats = (
            DashboardService
            .airline_flight_statistics(
                user.airline
            )
        )

    elif can_view_global_flights:
        visible_flights = (
            Flight.objects.all()
        )

    if is_admin or role == AIRPORT_MANAGER:
        visible_operations = (
            GroundOperation.objects.all()
        )

    elif role == GROUND_STAFF:
        visible_operations = (
            GroundOperation.objects.filter(
                assigned_staff=user
            )
        )

    recent_notifications = (
        Notification.objects
        .filter(user=user)
        .order_by(
            "-created_at"
        )[:5]
    )

    flight_stats = (
        DashboardService
        .flight_statistics(
            visible_flights
        )
    )

    operation_stats = (
        DashboardService
        .operation_statistics(
            visible_operations
        )
    )

    if can_view_security:
        security_stats = (
            DashboardService
            .security_statistics()
        )

        critical_security_reports = (
            DashboardService
            .critical_security_reports()
        )

    else:
        security_stats = {
            "total": 0,
            "open": 0,
            "investigating": 0,
            "critical": 0,
            "unassigned": 0,
        }

        critical_security_reports = []

    if can_view_passenger:
        passenger_stats = (
            DashboardService
            .passenger_statistics()
        )

        urgent_passenger_requests = (
            DashboardService
            .urgent_passenger_requests()
        )

    else:
        passenger_stats = {
            "total": 0,
            "open": 0,
            "assigned": 0,
            "in_progress": 0,
            "urgent": 0,
            "unassigned": 0,
            "completed": 0,
        }

        urgent_passenger_requests = []

    context = {
        "role": role,

        "is_admin": is_admin,

        "can_view_global_flights": (
            can_view_global_flights
        ),

        "can_view_operations": (
            can_view_global_operations
        ),

        "can_view_security": (
            can_view_security
        ),

        "can_view_passenger": (
            can_view_passenger
        ),

        "airline_stats": airline_stats,

        "flight_stats": flight_stats,

        "operation_stats": (
            operation_stats
        ),

        "security_stats": (
            security_stats
        ),

        "passenger_stats": (
            passenger_stats
        ),

        "recent_notifications": (
            recent_notifications
        ),

        "recent_flights": (
            DashboardService
            .recent_flights(
                visible_flights
            )
        ),

        "recent_operations": (
            DashboardService
            .recent_operations(
                visible_operations
            )
        ),

        "delayed_flights": (
            DashboardService
            .delayed_flights(
                visible_flights
            )
        ),

        "active_operations": (
            DashboardService
            .active_operations(
                visible_operations
            )
        ),

        "critical_security_reports": (
            critical_security_reports
        ),

        "urgent_passenger_requests": (
            urgent_passenger_requests
        ),
    }

    return render(
        request,
        "dashboard/index.html",
        context,
    )


def landing_page(request):
    context = {
        "overview": (
            LandingPageService
            .operational_overview()
        ),

        "featured_flights": (
            LandingPageService
            .featured_flights()
        ),
    }

    return render(
        request,
        "landing.html",
        context,
    )