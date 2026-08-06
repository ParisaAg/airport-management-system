from datetime import timedelta

from django.utils import timezone

from airports.models import Airport
from flights.models import Flight
from operations.models import GroundOperation
from passenger_service.models import PassengerRequest
from security.models import SecurityReport


class DashboardService:
    @staticmethod
    def flight_statistics():
        return {
            "total": Flight.objects.count(),

            "scheduled": Flight.objects.filter(
                status="SCHEDULED"
            ).count(),

            "boarding": Flight.objects.filter(
                status="BOARDING"
            ).count(),

            "delayed": Flight.objects.filter(
                status="DELAYED"
            ).count(),

            "cancelled": Flight.objects.filter(
                status="CANCELLED"
            ).count(),
        }

    @staticmethod
    def operation_statistics():
        return {
            "total": GroundOperation.objects.count(),

            "completed": GroundOperation.objects.filter(
                status="COMPLETED"
            ).count(),

            "in_progress": GroundOperation.objects.filter(
                status="IN_PROGRESS"
            ).count(),
        }

    @staticmethod
    def security_statistics():
        return {
            "total": SecurityReport.objects.count(),

            "critical": SecurityReport.objects.filter(
                severity="CRITICAL"
            ).count(),

            "open": SecurityReport.objects.filter(
                status="OPEN"
            ).count(),
        }

    @staticmethod
    def passenger_statistics():
        return {
            "total": PassengerRequest.objects.count(),

            "urgent": PassengerRequest.objects.filter(
                priority="URGENT"
            ).count(),

            "open": PassengerRequest.objects.filter(
                status="OPEN"
            ).count(),
        }

    @staticmethod
    def airline_flight_statistics(airline):
        return {
            "total": Flight.objects.filter(
                airline=airline
            ).count(),

            "delayed": Flight.objects.filter(
                airline=airline,
                status="DELAYED",
            ).count(),

            "cancelled": Flight.objects.filter(
                airline=airline,
                status="CANCELLED",
            ).count(),
        }


class LandingPageService:
    @staticmethod
    def operational_overview():
        today = timezone.localdate()

        todays_flights = Flight.objects.filter(
            departure_time__date=today
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