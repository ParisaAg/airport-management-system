from django.contrib.auth import get_user_model
from django.db.models import Q
from django.utils import timezone

from .models import Notification


DISRUPTION_RECIPIENT_ROLES = (
    "ADMIN",
    "AIRPORT_MANAGER",
    "GROUND_STAFF",
    "PASSENGER_SERVICE",
)


def notify_flight_disruption(
    *,
    flight,
    actor=None,
    delay_minutes=None,
):
    if flight.status not in {
        "DELAYED",
        "CANCELLED",
    }:
        return 0

    user_model = get_user_model()

    recipients = (
        user_model.objects
        .filter(is_active=True)
        .filter(
            Q(
                role__in=(
                    DISRUPTION_RECIPIENT_ROLES
                )
            )
            | Q(
                role="AIRLINE_OPERATOR",
                airline_id=flight.airline_id,
            )
        )
        .distinct()
    )

    if actor and actor.pk:
        recipients = recipients.exclude(
            pk=actor.pk,
        )

    reason = (
        flight.disruption_reason
        or "No operational reason provided."
    )

    if flight.status == "DELAYED":
        title = (
            f"Flight {flight.flight_number} delayed"
        )

        notification_type = "WARNING"

        estimated_departure = (
            flight.estimated_departure_time
        )

        if estimated_departure:
            local_departure = timezone.localtime(
                estimated_departure
            ).strftime(
                "%d %b %Y, %H:%M"
            )

            timing_message = (
                f" Estimated departure: "
                f"{local_departure}."
            )
        else:
            timing_message = ""

        delay_message = (
            f" Delay: {delay_minutes} minutes."
            if delay_minutes
            else ""
        )

        message = (
            f"Flight {flight.flight_number} "
            f"from {flight.origin.iata_code} "
            f"to {flight.destination.iata_code} "
            f"has been delayed."
            f"{delay_message}"
            f"{timing_message} "
            f"Reason: {reason}"
        )
    else:
        title = (
            f"Flight {flight.flight_number} cancelled"
        )

        notification_type = "ERROR"

        message = (
            f"Flight {flight.flight_number} "
            f"from {flight.origin.iata_code} "
            f"to {flight.destination.iata_code} "
            f"has been cancelled. "
            f"Reason: {reason}"
        )

    notifications = [
        Notification(
            user=user,
            title=title,
            message=message,
            notification_type=(
                notification_type
            ),
        )
        for user in recipients
    ]

    Notification.objects.bulk_create(
        notifications,
    )

    return len(notifications)