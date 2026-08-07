from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from audit.models import AuditLog
from audit.services import record_audit_event

from .models import SecurityReport


ALLOWED_SECURITY_TRANSITIONS = {
    "OPEN": {
        "INVESTIGATING",
    },
    "INVESTIGATING": {
        "RESOLVED",
    },
    "RESOLVED": {
        "INVESTIGATING",
        "CLOSED",
    },
    "CLOSED": set(),
}


class InvalidSecurityTransition(
    ValidationError
):
    pass


class InvalidSecurityAssignment(
    ValidationError
):
    pass


@transaction.atomic
def assign_security_officer(
    *,
    report_id,
    officer,
    actor=None,
    request=None,
):
    report = (
        SecurityReport.objects
        .select_for_update()
        .select_related(
            "flight",
            "officer",
        )
        .get(pk=report_id)
    )

    if (
        officer is None
        or not officer.is_active
        or officer.role != "SECURITY_OFFICER"
    ):
        raise InvalidSecurityAssignment(
            (
                "Security incidents can only "
                "be assigned to an active "
                "security officer."
            )
        )

    previous_officer = (
        report.officer.username
        if report.officer
        else None
    )

    if report.officer_id == officer.pk:
        return report

    report.officer = officer

    report.save(
        update_fields=[
            "officer",
            "updated_at",
        ]
    )

    record_audit_event(
        action=AuditLog.Action.ASSIGN,
        instance=report,
        actor=actor,
        request=request,
        description=(
            f"{report.reference} assigned "
            f"to {officer.username}."
        ),
        changes={
            "officer": {
                "from": previous_officer,
                "to": officer.username,
            }
        },
    )

    return report


@transaction.atomic
def transition_security_report_status(
    *,
    report_id,
    new_status,
    actor=None,
    request=None,
    resolution_notes="",
):
    report = (
        SecurityReport.objects
        .select_for_update()
        .select_related(
            "flight",
            "officer",
        )
        .get(pk=report_id)
    )

    valid_statuses = dict(
        SecurityReport.STATUS_CHOICES
    )

    if new_status not in valid_statuses:
        raise InvalidSecurityTransition(
            (
                "Unknown security incident "
                f"status: {new_status}"
            )
        )

    current_status = report.status

    allowed_statuses = (
        ALLOWED_SECURITY_TRANSITIONS.get(
            current_status,
            set(),
        )
    )

    if new_status not in allowed_statuses:
        raise InvalidSecurityTransition(
            (
                "Security incident cannot "
                f"transition from "
                f"{current_status} "
                f"to {new_status}."
            )
        )

    if (
        new_status == "INVESTIGATING"
        and not report.officer_id
    ):
        raise InvalidSecurityTransition(
            (
                "Assign a security officer "
                "before starting an "
                "investigation."
            )
        )

    cleaned_resolution_notes = (
        resolution_notes.strip()
    )

    if (
        new_status == "RESOLVED"
        and not cleaned_resolution_notes
    ):
        raise InvalidSecurityTransition(
            (
                "Resolution notes are required "
                "before resolving a security "
                "incident."
            )
        )

    changes = {
        "status": {
            "from": current_status,
            "to": new_status,
        }
    }

    update_fields = [
        "status",
        "status_updated_at",
        "updated_at",
    ]

    report.status = new_status
    report.status_updated_at = (
        timezone.now()
    )

    if new_status == "RESOLVED":
        report.resolution_notes = (
            cleaned_resolution_notes
        )

        report.resolved_at = (
            timezone.now()
        )

        changes["resolution_notes"] = {
            "from": "",
            "to": cleaned_resolution_notes,
        }

        update_fields.extend(
            [
                "resolution_notes",
                "resolved_at",
            ]
        )

    elif (
        current_status == "RESOLVED"
        and new_status == "INVESTIGATING"
    ):
        previous_resolved_at = (
            report.resolved_at.isoformat()
            if report.resolved_at
            else None
        )

        report.resolved_at = None

        changes["resolved_at"] = {
            "from": previous_resolved_at,
            "to": None,
        }

        update_fields.append(
            "resolved_at"
        )

    report.save(
        update_fields=update_fields
    )

    record_audit_event(
        action=(
            AuditLog.Action.STATUS_CHANGE
        ),
        instance=report,
        actor=actor,
        request=request,
        description=(
            f"{report.reference} changed "
            f"from {current_status} "
            f"to {new_status}."
        ),
        changes=changes,
    )

    return report


def available_security_status_choices(
    current_status,
):
    allowed_statuses = (
        ALLOWED_SECURITY_TRANSITIONS.get(
            current_status,
            set(),
        )
    )

    return [
        (value, label)
        for (
            value,
            label,
        ) in SecurityReport.STATUS_CHOICES
        if value in allowed_statuses
    ]