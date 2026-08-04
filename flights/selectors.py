from accounts.permissions import AIRLINE_OPERATOR
from datetime import timedelta

from django.db.models import Prefetch, Q
from django.utils import timezone

from .models import Flight, GateAssignment
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




def public_board_flights(
    *,
    airport,
    board_type="DEPARTURES",
):
    now = timezone.now()

    window_start = now - timedelta(hours=12)
    window_end = now + timedelta(hours=48)

    flights = (
        Flight.objects
        .select_related(
            "airline",
            "aircraft",
            "origin",
            "destination",
        )
        .prefetch_related(
            Prefetch(
                "gate_assignments",
                queryset=(
                    GateAssignment.objects
                    .filter(status="ACTIVE")
                    .select_related(
                        "gate",
                        "gate__terminal",
                    )
                    .order_by("-assigned_time")
                ),
                to_attr="active_gate_assignments",
            )
        )
        .filter(
            Q(departure_time__range=(
                window_start,
                window_end,
            ))
            | Q(arrival_time__range=(
                window_start,
                window_end,
            ))
        )
    )

    if board_type == "ARRIVALS":
        flights = flights.filter(
            destination=airport,
        ).order_by(
            "arrival_time",
        )
    else:
        flights = flights.filter(
            origin=airport,
        ).order_by(
            "departure_time",
        )

    return flights