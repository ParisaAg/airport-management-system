from accounts.permissions import AIRLINE_OPERATOR

from .models import Flight


def flights_visible_to(user):
    queryset = (
        Flight.objects
        .select_related(
            "airline",
            "aircraft",
            "aircraft__aircraft_type",
            "origin",
            "destination",
        )
        .all()
    )

    if (
        not user.is_superuser
        and user.role == AIRLINE_OPERATOR
    ):
        if not user.airline_id:
            return queryset.none()

        return queryset.filter(
            airline_id=user.airline_id,
        )

    return queryset