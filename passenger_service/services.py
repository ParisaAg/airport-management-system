from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from audit.models import AuditLog
from audit.services import record_audit_event

from .models import PassengerRequest


ALLOWED_PASSENGER_TRANSITIONS = {
    "OPEN": {
        "ASSIGNED",
        "CANCELLED",
    },
    "ASSIGNED": {
        "IN_PROGRESS",
        "CANCELLED",
    },
    "IN_PROGRESS": {
        "COMPLETED",
        "CANCELLED",
    },
    "COMPLETED": set(),
    "CANCELLED": set(),
}


class InvalidPassengerTransition(
    ValidationError
):
    pass


class InvalidPassengerAssignment(
    ValidationError
):
    pass


@transaction.atomic
def assign_passenger_request(
    *,
    request_id,
    staff,
    actor=None,
    request=None,
):
    passenger_request = (
        PassengerRequest.objects
        .select_for_update()
        .get(pk=request_id)
    )

    if passenger_request.status in {
        "COMPLETED",
        "CANCELLED",
    }:
        raise InvalidPassengerAssignment(
            (
                "Completed or cancelled requests "
                "cannot be reassigned."
            )
        )

    if (
        not staff
        or not staff.is_active
        or staff.role
        != "PASSENGER_SERVICE"
    ):
        raise InvalidPassengerAssignment(
            (
                "Requests can only be assigned "
                "to an active passenger service "
                "staff member."
            )
        )

    previous_staff = (
        passenger_request.assigned_staff
    )

    previous_status = (
        passenger_request.status
    )

    passenger_request.assigned_staff = (
        staff
    )

    update_fields = [
        "assigned_staff",
        "updated_at",
    ]

    if passenger_request.status == "OPEN":
        passenger_request.status = (
            "ASSIGNED"
        )

        passenger_request.status_updated_at = (
            timezone.now()
        )

        update_fields.extend(
            [
                "status",
                "status_updated_at",
            ]
        )

    passenger_request.save(
        update_fields=update_fields
    )

    record_audit_event(
        action=AuditLog.Action.ASSIGN,
        instance=passenger_request,
        actor=actor,
        request=request,
        description=(
            f"{passenger_request.reference} "
            f"assigned to {staff.username}."
        ),
        changes={
            "assigned_staff": {
                "from": (
                    previous_staff.username
                    if previous_staff
                    else None
                ),
                "to": staff.username,
            },
            "status": {
                "from": previous_status,
                "to": (
                    passenger_request.status
                ),
            },
        },
    )

    return passenger_request


@transaction.atomic
def transition_passenger_request_status(
    *,
    request_id,
    new_status,
    actor=None,
    request=None,
    resolution_notes="",
):
    passenger_request = (
        PassengerRequest.objects
        .select_for_update()
        .get(pk=request_id)
    )

    valid_statuses = dict(
        PassengerRequest.STATUS_CHOICES
    )

    if new_status not in valid_statuses:
        raise InvalidPassengerTransition(
            (
                "Unknown passenger request "
                f"status: {new_status}"
            )
        )

    current_status = (
        passenger_request.status
    )

    allowed_statuses = (
        ALLOWED_PASSENGER_TRANSITIONS.get(
            current_status,
            set(),
        )
    )

    if new_status not in allowed_statuses:
        raise InvalidPassengerTransition(
            (
                "Passenger request cannot "
                f"transition from "
                f"{current_status} "
                f"to {new_status}."
            )
        )

    if (
        new_status
        in {
            "ASSIGNED",
            "IN_PROGRESS",
        }
        and not passenger_request.assigned_staff_id
    ):
        raise InvalidPassengerTransition(
            (
                "A passenger service staff "
                "member must be assigned first."
            )
        )

    cleaned_resolution = (
        resolution_notes.strip()
        if resolution_notes
        else ""
    )

    if (
        new_status == "COMPLETED"
        and not cleaned_resolution
    ):
        raise InvalidPassengerTransition(
            (
                "Resolution notes are required "
                "before completing a passenger "
                "request."
            )
        )

    passenger_request.status = (
        new_status
    )

    passenger_request.status_updated_at = (
        timezone.now()
    )

    update_fields = [
        "status",
        "status_updated_at",
        "updated_at",
    ]

    changes = {
        "status": {
            "from": current_status,
            "to": new_status,
        },
    }

    if new_status == "COMPLETED":
        passenger_request.resolution_notes = (
            cleaned_resolution
        )

        passenger_request.completed_at = (
            timezone.now()
        )

        update_fields.extend(
            [
                "resolution_notes",
                "completed_at",
            ]
        )

        changes["resolution_notes"] = {
            "from": None,
            "to": cleaned_resolution,
        }

    passenger_request.save(
        update_fields=update_fields
    )

    record_audit_event(
        action=(
            AuditLog.Action.STATUS_CHANGE
        ),
        instance=passenger_request,
        actor=actor,
        request=request,
        description=(
            f"{passenger_request.reference} "
            f"changed from "
            f"{current_status} "
            f"to {new_status}."
        ),
        changes=changes,
    )

    return passenger_request


def available_passenger_status_choices(
    current_status,
):
    allowed_statuses = (
        ALLOWED_PASSENGER_TRANSITIONS.get(
            current_status,
            set(),
        )
    )

    return [
        (value, label)
        for value, label
        in PassengerRequest.STATUS_CHOICES
        if value in allowed_statuses
    ]