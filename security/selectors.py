from django.db.models import Q

from .models import SecurityReport


ACTIVE_SECURITY_STATUSES = (
    "OPEN",
    "INVESTIGATING",
)


def security_reports_visible_to(user):
    return (
        SecurityReport.objects
        .select_related(
            "flight",
            "flight__airline",
            "flight__origin",
            "flight__destination",
            "officer",
        )
        .all()
    )


def filter_security_reports(
    queryset,
    *,
    search="",
    status="",
    severity="",
    report_type="",
    assignment="",
    user=None,
):
    if search:
        query = (
            Q(
                flight__flight_number__icontains=search
            )
            | Q(
                description__icontains=search
            )
            | Q(
                location__icontains=search
            )
            | Q(
                officer__username__icontains=search
            )
        )

        normalized_reference = (
            search.upper()
            .replace("SEC-", "")
        )

        if normalized_reference.isdigit():
            query |= Q(
                pk=int(
                    normalized_reference
                )
            )

        queryset = queryset.filter(
            query
        )

    if status in dict(
        SecurityReport.STATUS_CHOICES
    ):
        queryset = queryset.filter(
            status=status
        )

    if severity in dict(
        SecurityReport.SEVERITY_CHOICES
    ):
        queryset = queryset.filter(
            severity=severity
        )

    if report_type in dict(
        SecurityReport.REPORT_TYPE_CHOICES
    ):
        queryset = queryset.filter(
            report_type=report_type
        )

    if assignment == "UNASSIGNED":
        queryset = queryset.filter(
            officer__isnull=True
        )

    elif (
        assignment == "MINE"
        and user is not None
    ):
        queryset = queryset.filter(
            officer=user
        )

    return queryset


def security_statistics(queryset):
    active_queryset = queryset.filter(
        status__in=(
            ACTIVE_SECURITY_STATUSES
        )
    )

    return {
        "open": queryset.filter(
            status="OPEN"
        ).count(),

        "investigating": queryset.filter(
            status="INVESTIGATING"
        ).count(),

        "critical": active_queryset.filter(
            severity="CRITICAL"
        ).count(),

        "unassigned": active_queryset.filter(
            officer__isnull=True
        ).count(),
    }