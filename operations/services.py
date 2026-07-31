from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

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


class InvalidOperationTransition(ValidationError):
    pass


@transaction.atomic
def transition_ground_operation(
    *,
    operation_id,
    new_status,
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

    if new_status not in dict(
        GroundOperation.STATUS_CHOICES
    ):
        raise InvalidOperationTransition(
            f"Unknown operation status: {new_status}"
        )

    allowed_statuses = ALLOWED_STATUS_TRANSITIONS.get(
        current_status,
        set(),
    )

    if new_status not in allowed_statuses:
        raise InvalidOperationTransition(
            (
                "Ground operation cannot transition "
                f"from {current_status} to {new_status}."
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
            operation.start_time or current_time
        )
        update_fields.append("start_time")

    if new_status == "COMPLETED":
        operation.end_time = current_time
        update_fields.append("end_time")

    operation.full_clean()

    operation.save(update_fields=update_fields)

    return operation