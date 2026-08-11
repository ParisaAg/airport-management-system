from django.db.models import Q

from .models import PassengerRequest


ACTIVE_PASSENGER_STATUSES = (
    "OPEN",
    "ASSIGNED",
    "IN_PROGRESS",
)


def passenger_requests_visible_to(
    user,
):
    return (
        PassengerRequest.objects
        .select_related(
            "flight",
            "flight__airline",
            "flight__origin",
            "flight__destination",
            "assigned_staff",
        )
        .all()
    )


def filter_passenger_requests(
    queryset,
    *,
    search="",
    status="",
    priority="",
    request_type="",
    assignment="",
    user=None,
):
    search = search.strip()

    if search:
        search_query = (
            Q(
                passenger_name__icontains=search
            )
            | Q(
                booking_reference__icontains=search
            )
            | Q(
                flight__flight_number__icontains=search
            )
            | Q(
                service_location__icontains=search
            )
            | Q(
                description__icontains=search
            )
            | Q(
                assigned_staff__username__icontains=search
            )
        )

        normalized_reference = (
            search.upper()
        )

        if normalized_reference.startswith(
            "PSR-"
        ):
            reference_id = (
                normalized_reference
                .removeprefix("PSR-")
            )

            if reference_id.isdigit():
                search_query |= Q(
                    pk=int(reference_id)
                )

        queryset = queryset.filter(
            search_query
        )

    valid_statuses = dict(
        PassengerRequest.STATUS_CHOICES
    )

    if status in valid_statuses:
        queryset = queryset.filter(
            status=status
        )

    valid_priorities = dict(
        PassengerRequest.PRIORITY_CHOICES
    )

    if priority in valid_priorities:
        queryset = queryset.filter(
            priority=priority
        )

    valid_request_types = dict(
        PassengerRequest
        .REQUEST_TYPE_CHOICES
    )

    if request_type in valid_request_types:
        queryset = queryset.filter(
            request_type=request_type
        )

    if assignment == "UNASSIGNED":
        queryset = queryset.filter(
            assigned_staff__isnull=True
        )

    elif (
        assignment == "MINE"
        and user
        and user.is_authenticated
    ):
        queryset = queryset.filter(
            assigned_staff=user
        )

    return queryset


def passenger_statistics(
    queryset,
):
    active_requests = queryset.filter(
        status__in=(
            ACTIVE_PASSENGER_STATUSES
        )
    )

    return {
        "open": queryset.filter(
            status="OPEN"
        ).count(),

        "in_progress": queryset.filter(
            status="IN_PROGRESS"
        ).count(),

        "urgent": active_requests.filter(
            priority="URGENT"
        ).count(),

        "unassigned": active_requests.filter(
            assigned_staff__isnull=True
        ).count(),
    }