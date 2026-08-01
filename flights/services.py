from django.core.exceptions import ValidationError
from django.db import transaction

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


@transaction.atomic
def transition_flight_status(
    *,
    flight_id,
    new_status,
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

    if new_status not in dict(
        Flight.STATUS_CHOICES
    ):
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

    flight.status = new_status

    flight.save(
        update_fields=[
            "status",
            "updated_at",
        ]
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
        for value, label in Flight.STATUS_CHOICES
        if value in allowed_statuses
    ]