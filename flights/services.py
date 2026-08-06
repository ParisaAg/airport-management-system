from datetime import timedelta
from notifications.services import (notify_flight_disruption,)
from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from audit.models import AuditLog
from audit.services import record_audit_event

from .models import Flight


ALLOWED_FLIGHT_TRANSITIONS = {
    "SCHEDULED": {
        "BOARDING",
        "DELAYED",
        "CANCELLED",
    },
    "DELAYED": {
        "SCHEDULED",
        "BOARDING",
        "CANCELLED",
    },
    "BOARDING": {
        "DEPARTED",
        "DELAYED",
        "CANCELLED",
    },
    "DEPARTED": {
        "ARRIVED",
    },
    "ARRIVED": set(),
    "CANCELLED": set(),
}


class InvalidFlightTransition(ValidationError):
    pass


def _serialize_datetime(value):
    if value is None:
        return None

    return value.isoformat()


def _validate_disruption_details(
    *,
    new_status,
    delay_minutes,
    reason,
):
    reason = (reason or "").strip()

    if new_status == "DELAYED":
        if not reason:
            raise InvalidFlightTransition(
                "A delay reason is required."
            )

        try:
            delay_minutes = int(
                delay_minutes
            )
        except (TypeError, ValueError):
            raise InvalidFlightTransition(
                "A valid delay duration is required."
            )

        if not 1 <= delay_minutes <= 1440:
            raise InvalidFlightTransition(
                (
                    "Delay duration must be between "
                    "1 and 1440 minutes."
                )
            )

    if (
        new_status == "CANCELLED"
        and not reason
    ):
        raise InvalidFlightTransition(
            "A cancellation reason is required."
        )

    return delay_minutes, reason


@transaction.atomic
def transition_flight_status(
    *,
    flight_id,
    new_status,
    actor=None,
    request=None,
    delay_minutes=None,
    reason="",
):
    flight = (
        Flight.objects
        .select_for_update()
        .select_related(
            "airline",
            "aircraft",
            "origin",
            "destination",
        )
        .get(pk=flight_id)
    )

    valid_statuses = dict(
        Flight.STATUS_CHOICES
    )

    if new_status not in valid_statuses:
        raise InvalidFlightTransition(
            f"Unknown flight status: {new_status}"
        )

    current_status = flight.status

    allowed_statuses = (
        ALLOWED_FLIGHT_TRANSITIONS.get(
            current_status,
            set(),
        )
    )

    if new_status not in allowed_statuses:
        raise InvalidFlightTransition(
            (
                "Flight cannot transition "
                f"from {current_status} "
                f"to {new_status}."
            )
        )

    delay_minutes, reason = (
        _validate_disruption_details(
            new_status=new_status,
            delay_minutes=delay_minutes,
            reason=reason,
        )
    )

    now = timezone.now()

    previous_estimated_departure = (
        flight.estimated_departure_time
    )

    previous_estimated_arrival = (
        flight.estimated_arrival_time
    )

    previous_reason = (
        flight.disruption_reason
    )

    changes = {
        "status": {
            "from": current_status,
            "to": new_status,
        }
    }

    update_fields = {
        "status",
        "status_updated_at",
        "updated_at",
    }

    flight.status = new_status
    flight.status_updated_at = now

    if new_status == "DELAYED":
        delay = timedelta(
            minutes=delay_minutes,
        )

        flight.estimated_departure_time = (
            flight.departure_time + delay
        )

        flight.estimated_arrival_time = (
            flight.arrival_time + delay
        )

        flight.disruption_reason = reason

        update_fields.update(
            {
                "estimated_departure_time",
                "estimated_arrival_time",
                "disruption_reason",
            }
        )

        changes.update(
            {
                "delay_minutes": {
                    "from": None,
                    "to": delay_minutes,
                },
                "estimated_departure_time": {
                    "from": _serialize_datetime(
                        previous_estimated_departure
                    ),
                    "to": _serialize_datetime(
                        flight.estimated_departure_time
                    ),
                },
                "estimated_arrival_time": {
                    "from": _serialize_datetime(
                        previous_estimated_arrival
                    ),
                    "to": _serialize_datetime(
                        flight.estimated_arrival_time
                    ),
                },
                "reason": {
                    "from": previous_reason,
                    "to": reason,
                },
            }
        )

    elif new_status == "CANCELLED":
        flight.disruption_reason = reason

        update_fields.add(
            "disruption_reason"
        )

        changes["reason"] = {
            "from": previous_reason,
            "to": reason,
        }

    elif new_status == "SCHEDULED":
        flight.estimated_departure_time = None
        flight.estimated_arrival_time = None
        flight.disruption_reason = ""

        update_fields.update(
            {
                "estimated_departure_time",
                "estimated_arrival_time",
                "disruption_reason",
            }
        )

        changes.update(
            {
                "estimated_departure_time": {
                    "from": _serialize_datetime(
                        previous_estimated_departure
                    ),
                    "to": None,
                },
                "estimated_arrival_time": {
                    "from": _serialize_datetime(
                        previous_estimated_arrival
                    ),
                    "to": None,
                },
                "reason": {
                    "from": previous_reason,
                    "to": "",
                },
            }
        )

    elif new_status == "DEPARTED":
        flight.actual_departure_time = now

        update_fields.add(
            "actual_departure_time"
        )

        changes["actual_departure_time"] = {
            "from": None,
            "to": _serialize_datetime(now),
        }

    elif new_status == "ARRIVED":
        flight.actual_arrival_time = now

        update_fields.add(
            "actual_arrival_time"
        )

        changes["actual_arrival_time"] = {
            "from": None,
            "to": _serialize_datetime(now),
        }

    flight.save(
        update_fields=list(update_fields),
    )

    record_audit_event(
        action=AuditLog.Action.STATUS_CHANGE,
        instance=flight,
        actor=actor,
        request=request,
        description=(
            f"Flight {flight.flight_number} "
            f"changed from {current_status} "
            f"to {new_status}."
        ),
        changes=changes,
    )
    if new_status in {
        "DELAYED",
        "CANCELLED",
    }:
        notify_flight_disruption(
            flight=flight,
            actor=actor,
            delay_minutes=delay_minutes,
        )
    return flight


def available_flight_status_choices(
    current_status,
):
    allowed_statuses = (
        ALLOWED_FLIGHT_TRANSITIONS.get(
            current_status,
            set(),
        )
    )

    return [
        (value, label)
        for value, label
        in Flight.STATUS_CHOICES
        if value in allowed_statuses
    ]