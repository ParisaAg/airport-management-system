from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST
from .services import (
    InvalidFlightTransition,
    transition_flight_status,
)
from .services import (
    InvalidFlightTransition,
    available_flight_status_choices,
    transition_flight_status,
)
from accounts.permissions import (
    ADMIN,
    AIRLINE_OPERATOR,
    role_required,
)

from .forms import FlightForm, GateAssignmentForm
from .models import Flight, GateAssignment
from .selectors import flights_visible_to


FLIGHT_MANAGEMENT_ROLES = (
    ADMIN,
    AIRLINE_OPERATOR,
)


@login_required
def flight_list(request):
    flights = flights_visible_to(
        request.user
    )

    search = request.GET.get(
        "search",
        "",
    ).strip()

    status = request.GET.get(
        "status",
        "",
    ).strip()

    if search:
        flights = flights.filter(
            flight_number__icontains=search,
        )

    if status in dict(
        Flight.STATUS_CHOICES
    ):
        flights = flights.filter(
            status=status,
        )

    return render(
        request,
        "flights/list.html",
        {
            "flights": flights,
            "statuses": Flight.STATUS_CHOICES,
        },
    )


@login_required
@role_required(*FLIGHT_MANAGEMENT_ROLES)
def flight_create(request):
    if (
        request.user.role == AIRLINE_OPERATOR
        and not request.user.airline_id
    ):
        raise PermissionDenied

    if request.method == "POST":
        form = FlightForm(
            request.POST,
            user=request.user,
        )

        if form.is_valid():
            flight = form.save(
                commit=False,
            )

            if (
                request.user.role
                == AIRLINE_OPERATOR
            ):
                flight.airline = (
                    request.user.airline
                )

            flight.save()

            messages.success(
                request,
                (
                    f"Flight {flight.flight_number} "
                    "created successfully."
                ),
            )

            return redirect("flight_list")
    else:
        form = FlightForm(
            user=request.user,
        )

    return render(
        request,
        "flights/create.html",
        {
            "form": form,
            "edit": False,
        },
    )


@login_required
@role_required(*FLIGHT_MANAGEMENT_ROLES)
def flight_edit(request, id):
    flight = get_object_or_404(
        flights_visible_to(request.user),
        id=id,
    )

    if request.method == "POST":
        form = FlightForm(
            request.POST,
            instance=flight,
            user=request.user,
        )

        if form.is_valid():
            flight = form.save()

            messages.success(
                request,
                (
                    f"Flight {flight.flight_number} "
                    "updated successfully."
                ),
            )

            return redirect(
                "flight_detail",
                id=flight.id,
            )
    else:
        form = FlightForm(
            instance=flight,
            user=request.user,
        )

    return render(
        request,
        "flights/create.html",
        {
            "form": form,
            "edit": True,
            "flight": flight,
        },
    )


@login_required
@role_required(ADMIN)
def flight_delete(request, id):
    flight = get_object_or_404(
        Flight,
        id=id,
    )

    if request.method == "POST":
        flight_number = (
            flight.flight_number
        )

        flight.delete()

        messages.success(
            request,
            (
                f"Flight {flight_number} "
                "deleted successfully."
            ),
        )

        return redirect("flight_list")

    return render(
        request,
        "flights/delete.html",
        {
            "flight": flight,
        },
    )


@login_required
def flight_detail(request, id):
    flight = get_object_or_404(
        flights_visible_to(request.user),
        id=id,
    )

    gate_assignments = (
        flight.gate_assignments
        .select_related(
            "gate",
            "gate__terminal",
            "gate__terminal__airport",
        )
        .all()
    )
    
    ground_operations = (
        flight.ground_operations
        .select_related(
            "operation_type",
            "assigned_staff",
        )
        .all()
    )

    return render(
        request,
        "flights/detail.html",
        {
            "flight": flight,
            "statuses": Flight.STATUS_CHOICES,
            "gate_assignments": gate_assignments,
            "ground_operations": ground_operations,
            "allowed_statuses": (available_flight_status_choices(flight.status)),
        },
    )


@login_required
@require_POST
@role_required(ADMIN)
def flight_change_status(request, id):
    flight = get_object_or_404(
        Flight,
        id=id,
    )

    new_status = request.POST.get(
        "status"
    )

    try:
        flight = transition_flight_status(
            flight_id=flight.id,
            new_status=new_status,
        )
    except InvalidFlightTransition as error:
        messages.error(
            request,
            error.messages[0],
        )
    else:
        messages.success(
            request,
            (
                f"Flight {flight.flight_number} "
                f"changed to "
                f"{flight.get_status_display()}."
            ),
        )

    return redirect(
        "flight_detail",
        id=flight.id,
    )


@login_required
@role_required(ADMIN)
def gate_assignment_create(request, id):
    flight = get_object_or_404(
        Flight,
        id=id,
    )

    if request.method == "POST":
        form = GateAssignmentForm(
            request.POST,
        )

        if form.is_valid():
            assignment = form.save(
                commit=False,
            )

            assignment.flight = flight
            assignment.save()

            messages.success(
                request,
                (
                    f"Gate {assignment.gate.code} "
                    f"assigned to {flight.flight_number}."
                ),
            )

            return redirect(
                "flight_detail",
                id=flight.id,
            )
    else:
        form = GateAssignmentForm()

    return render(
        request,
        "flights/gate_assignment_form.html",
        {
            "form": form,
            "flight": flight,
        },
    )


@login_required
@require_POST
@role_required(ADMIN)
def gate_assignment_release(request, id):
    assignment = get_object_or_404(
        GateAssignment.objects.select_related(
            "flight",
            "gate",
        ),
        id=id,
    )

    if assignment.status == "ACTIVE":
        from django.utils import timezone

        assignment.status = "RELEASED"
        assignment.released_time = (
            timezone.now()
        )

        assignment.save(
            update_fields=[
                "status",
                "released_time",
            ]
        )

        messages.success(
            request,
            (
                f"Gate {assignment.gate.code} "
                "released successfully."
            ),
        )

    return redirect(
        "flight_detail",
        id=assignment.flight_id,
    )