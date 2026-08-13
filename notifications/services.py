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

OPERATION_RECIPIENT_ROLES = (
    "ADMIN",
    "AIRPORT_MANAGER",
)

SECURITY_RECIPIENT_ROLES = (
    "ADMIN",
    "AIRPORT_MANAGER",
    "SECURITY_OFFICER",
)

PASSENGER_RECIPIENT_ROLES = (
    "ADMIN",
    "AIRPORT_MANAGER",
    "PASSENGER_SERVICE",
)

GATE_RECIPIENT_ROLES = (
    "ADMIN",
    "AIRPORT_MANAGER",
    "GROUND_STAFF",
)


def create_notifications(
    *,
    recipients,
    title,
    message,
    notification_type="INFO",
    actor=None,
):
    valid_types = dict(
        Notification.TYPE_CHOICES
    )

    if notification_type not in valid_types:
        raise ValueError(
            (
                "Unknown notification type: "
                f"{notification_type}"
            )
        )

    recipients = recipients.filter(
        is_active=True,
    )

    if actor and actor.pk:
        recipients = recipients.exclude(
            pk=actor.pk,
        )

    recipient_ids = (
        recipients
        .order_by()
        .values_list(
            "pk",
            flat=True,
        )
        .distinct()
    )

    notifications = [
        Notification(
            user_id=user_id,
            title=title,
            message=message,
            notification_type=(
                notification_type
            ),
        )
        for user_id in recipient_ids
    ]

    if not notifications:
        return 0

    Notification.objects.bulk_create(
        notifications,
    )

    return len(notifications)


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
    )

    reason = (
        flight.disruption_reason
        or "No operational reason provided."
    )

    route = (
        f"{flight.origin.iata_code} "
        f"to {flight.destination.iata_code}"
    )

    if flight.status == "DELAYED":
        title = (
            f"Flight {flight.flight_number} delayed"
        )

        notification_type = "WARNING"

        if flight.estimated_departure_time:
            local_departure = (
                timezone.localtime(
                    flight.estimated_departure_time
                )
                .strftime(
                    "%d %b %Y, %H:%M"
                )
            )

            timing_message = (
                " Estimated departure: "
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
            f"from {route} has been delayed."
            f"{delay_message}"
            f"{timing_message} "
            f"Reason: {reason}"
        )
    else:
        title = (
            f"Flight {flight.flight_number} "
            "cancelled"
        )

        notification_type = "ERROR"

        message = (
            f"Flight {flight.flight_number} "
            f"from {route} has been cancelled. "
            f"Reason: {reason}"
        )

    return create_notifications(
        recipients=recipients,
        title=title,
        message=message,
        notification_type=(
            notification_type
        ),
        actor=actor,
    )


def notify_ground_operation_completed(
    *,
    operation,
    actor=None,
):
    if operation.status != "COMPLETED":
        return 0

    user_model = get_user_model()

    recipients = (
        user_model.objects
        .filter(
            Q(
                role__in=(
                    OPERATION_RECIPIENT_ROLES
                )
            )
            | Q(
                pk=operation.assigned_staff_id,
            )
        )
    )

    return create_notifications(
        recipients=recipients,
        title="Ground operation completed",
        message=(
            f"{operation.operation_type.name} "
            f"for flight "
            f"{operation.flight.flight_number} "
            "has been completed."
        ),
        notification_type="SUCCESS",
        actor=actor,
    )


def notify_gate_changed(
    *,
    assignment,
    previous_gate_code,
    actor=None,
):
    user_model = get_user_model()

    recipients = (
        user_model.objects
        .filter(
            Q(
                role__in=(
                    GATE_RECIPIENT_ROLES
                )
            )
            | Q(
                role="AIRLINE_OPERATOR",
                airline_id=(
                    assignment.flight.airline_id
                ),
            )
        )
    )

    return create_notifications(
        recipients=recipients,
        title="Flight gate changed",
        message=(
            f"Flight "
            f"{assignment.flight.flight_number} "
            f"gate changed from "
            f"{previous_gate_code} "
            f"to {assignment.gate.code}."
        ),
        notification_type="WARNING",
        actor=actor,
    )


def notify_critical_security_report(
    *,
    report,
    actor=None,
):
    if report.severity != "CRITICAL":
        return 0

    user_model = get_user_model()

    recipients = (
        user_model.objects
        .filter(
            role__in=(
                SECURITY_RECIPIENT_ROLES
            )
        )
    )

    flight_context = (
        f" for flight "
        f"{report.flight.flight_number}"
        if report.flight_id
        else ""
    )

    return create_notifications(
        recipients=recipients,
        title="Critical security incident",
        message=(
            f"{report.reference}: critical "
            f"security incident reported"
            f"{flight_context}. "
            f"Location: "
            f"{report.location or 'Not specified'}."
        ),
        notification_type="ERROR",
        actor=actor,
    )


def notify_urgent_passenger_request(
    *,
    passenger_request,
    actor=None,
):
    if passenger_request.priority != "URGENT":
        return 0

    user_model = get_user_model()

    recipients = (
        user_model.objects
        .filter(
            role__in=(
                PASSENGER_RECIPIENT_ROLES
            )
        )
    )

    return create_notifications(
        recipients=recipients,
        title="Urgent passenger request",
        message=(
            f"{passenger_request.reference}: "
            f"urgent "
            f"{passenger_request.get_request_type_display()} "
            f"request for passenger "
            f"{passenger_request.passenger_name} "
            f"on flight "
            f"{passenger_request.flight.flight_number}."
        ),
        notification_type="WARNING",
        actor=actor,
    )