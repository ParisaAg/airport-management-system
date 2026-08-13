from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from audit.models import AuditLog
from audit.services import record_audit_event
from notifications.services import (
    notify_ground_operation_completed,
)

from .models import GroundOperation


ALLOWED_STATUS_TRANSITIONS = {
    "PENDING": {
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


class InvalidOperationTransition(
    ValidationError
):
    pass


@transaction.atomic
def transition_ground_operation(
    *,
    operation_id,
    new_status,
    actor=None,
    request=None,
):
    operation = (
        GroundOperation.objects
        .select_for_update()
        .select_related(
            "flight",
            "operation_type",
            "assigned_staff",
        )
        .get(pk=operation_id)
    )

    current_status = operation.status

    valid_statuses = dict(
        GroundOperation.STATUS_CHOICES
    )

    if new_status not in valid_statuses:
        raise InvalidOperationTransition(
            (
                "Unknown operation status: "
                f"{new_status}"
            )
        )

    allowed_statuses = (
        ALLOWED_STATUS_TRANSITIONS.get(
            current_status,
            set(),
        )
    )

    if new_status not in allowed_statuses:
        raise InvalidOperationTransition(
            (
                "Ground operation cannot "
                f"transition from "
                f"{current_status} "
                f"to {new_status}."
            )
        )

    current_time = timezone.now()

    operation.status = new_status

    update_fields = [
        "status",
        "updated_at",
    ]

    if new_status == "IN_PROGRESS":
        operation.start_time = (
            operation.start_time
            or current_time
        )

        update_fields.append(
            "start_time"
        )

    if new_status == "COMPLETED":
        operation.end_time = current_time

        update_fields.append(
            "end_time"
        )

    operation.full_clean()

    operation.save(
        update_fields=update_fields
    )

    record_audit_event(
        action=(
            AuditLog.Action.STATUS_CHANGE
        ),
        instance=operation,
        actor=actor,
        request=request,
        description=(
            "Ground operation "
            f"{operation.operation_type.name} "
            f"changed from {current_status} "
            f"to {new_status}."
        ),
        changes={
            "status": {
                "from": current_status,
                "to": new_status,
            }
        },
    )

    if new_status == "COMPLETED":
        notify_ground_operation_completed(
            operation=operation,
            actor=actor,
        )

    return operation