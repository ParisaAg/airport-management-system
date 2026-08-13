from datetime import timedelta

from django.utils import timezone

from airports.models import Airport

from flights.models import Flight
from operations.models import GroundOperation
from passenger_service.models import (
    PassengerRequest,
)
from security.models import SecurityReport


ACTIVE_SECURITY_STATUSES = (
    "OPEN",
    "INVESTIGATING",
)


ACTIVE_PASSENGER_STATUSES = (
    "OPEN",
    "ASSIGNED",
    "IN_PROGRESS",
)


class DashboardService:

    @staticmethod
    def flight_statistics(
        queryset=None,
    ):
        if queryset is None:
            queryset = Flight.objects.all()

        return {
            "total": queryset.count(),

            "scheduled": queryset.filter(
                status="SCHEDULED"
            ).count(),

            "boarding": queryset.filter(
                status="BOARDING"
            ).count(),

            "delayed": queryset.filter(
                status="DELAYED"
            ).count(),

            "departed": queryset.filter(
                status="DEPARTED"
            ).count(),

            "arrived": queryset.filter(
                status="ARRIVED"
            ).count(),

            "cancelled": queryset.filter(
                status="CANCELLED"
            ).count(),
        }

    @staticmethod
    def operation_statistics(
        queryset=None,
    ):
        if queryset is None:
            queryset = (
                GroundOperation.objects.all()
            )

        return {
            "total": queryset.count(),

            "pending": queryset.filter(
                status="PENDING"
            ).count(),

            "in_progress": queryset.filter(
                status="IN_PROGRESS"
            ).count(),

            "completed": queryset.filter(
                status="COMPLETED"
            ).count(),

            "cancelled": queryset.filter(
                status="CANCELLED"
            ).count(),
        }

    @staticmethod
    def security_statistics(
        queryset=None,
    ):
        if queryset is None:
            queryset = (
                SecurityReport.objects.all()
            )

        active_reports = queryset.filter(
            status__in=(
                ACTIVE_SECURITY_STATUSES
            )
        )

        return {
            "total": queryset.count(),

            "open": queryset.filter(
                status="OPEN"
            ).count(),

            "investigating": (
                queryset.filter(
                    status="INVESTIGATING"
                ).count()
            ),

            "critical": (
                active_reports.filter(
                    severity="CRITICAL"
                ).count()
            ),

            "unassigned": (
                active_reports.filter(
                    officer__isnull=True
                ).count()
            ),
        }

    @staticmethod
    def passenger_statistics(
        queryset=None,
    ):
        if queryset is None:
            queryset = (
                PassengerRequest.objects.all()
            )

        active_requests = queryset.filter(
            status__in=(
                ACTIVE_PASSENGER_STATUSES
            )
        )

        return {
            "total": queryset.count(),

            "open": queryset.filter(
                status="OPEN"
            ).count(),

            "assigned": queryset.filter(
                status="ASSIGNED"
            ).count(),

            "in_progress": queryset.filter(
                status="IN_PROGRESS"
            ).count(),

            "urgent": (
                active_requests.filter(
                    priority="URGENT"
                ).count()
            ),

            "unassigned": (
                active_requests.filter(
                    assigned_staff__isnull=True
                ).count()
            ),

            "completed": queryset.filter(
                status="COMPLETED"
            ).count(),
        }

    @staticmethod
    def airline_flight_statistics(
        airline,
    ):
        flights = Flight.objects.filter(
            airline=airline
        )

        return (
            DashboardService
            .flight_statistics(flights)
        )

    @staticmethod
    def recent_flights(
        queryset=None,
        *,
        limit=5,
    ):
        if queryset is None:
            queryset = Flight.objects.all()

        return (
            queryset
            .select_related(
                "airline",
                "aircraft",
                "origin",
                "destination",
            )
            .order_by(
                "-updated_at"
            )[:limit]
        )

    @staticmethod
    def recent_operations(
        queryset=None,
        *,
        limit=5,
    ):
        if queryset is None:
            queryset = (
                GroundOperation.objects.all()
            )

        return (
            queryset
            .select_related(
                "flight",
                "operation_type",
                "assigned_staff",
            )
            .order_by(
                "-updated_at"
            )[:limit]
        )

    @staticmethod
    def delayed_flights(
        queryset=None,
        *,
        limit=5,
    ):
        if queryset is None:
            queryset = Flight.objects.all()

        return (
            queryset
            .select_related(
                "airline",
                "origin",
                "destination",
            )
            .filter(
                status="DELAYED"
            )
            .order_by(
                "departure_time"
            )[:limit]
        )

    @staticmethod
    def critical_security_reports(
        *,
        limit=5,
    ):
        return (
            SecurityReport.objects
            .select_related(
                "flight",
                "officer",
            )
            .filter(
                status__in=(
                    ACTIVE_SECURITY_STATUSES
                ),
                severity="CRITICAL",
            )
            .order_by(
                "-created_at"
            )[:limit]
        )

    @staticmethod
    def urgent_passenger_requests(
        *,
        limit=5,
    ):
        return (
            PassengerRequest.objects
            .select_related(
                "flight",
                "assigned_staff",
            )
            .filter(
                status__in=(
                    ACTIVE_PASSENGER_STATUSES
                ),
                priority="URGENT",
            )
            .order_by(
                "-created_at"
            )[:limit]
        )

    @staticmethod
    def active_operations(
        queryset=None,
        *,
        limit=5,
    ):
        if queryset is None:
            queryset = (
                GroundOperation.objects.all()
            )

        return (
            queryset
            .select_related(
                "flight",
                "operation_type",
                "assigned_staff",
            )
            .filter(
                status__in=(
                    "PENDING",
                    "IN_PROGRESS",
                )
            )
            .order_by(
                "status",
                "-updated_at",
            )[:limit]
        )


class LandingPageService:

    @staticmethod
    def operational_overview():
        today = timezone.localdate()

        todays_flights = (
            Flight.objects.filter(
                departure_time__date=today
            )
        )

        return {
            "flights_today": (
                todays_flights.count()
            ),

            "active_operations": (
                GroundOperation.objects.filter(
                    status="IN_PROGRESS"
                ).count()
            ),

            "delayed_flights": (
                todays_flights.filter(
                    status="DELAYED"
                ).count()
            ),

            "airports": (
                Airport.objects.count()
            ),
        }

    @staticmethod
    def featured_flights():
        now = timezone.now()

        window_start = (
            now - timedelta(hours=3)
        )

        window_end = (
            now + timedelta(hours=12)
        )

        return (
            Flight.objects
            .select_related(
                "airline",
                "origin",
                "destination",
            )
            .filter(
                departure_time__range=(
                    window_start,
                    window_end,
                )
            )
            .exclude(
                status="CANCELLED"
            )
            .order_by(
                "departure_time"
            )[:5]
        )