from django.contrib import messages
from airports.models import Airport
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_GET, require_POST
from django.http import JsonResponse
from accounts.permissions import (ADMIN,AIRLINE_OPERATOR,role_required,)
from .selectors import (flights_visible_to,public_board_flights,)
from audit.models import AuditLog
from audit.services import record_audit_event
from .forms import FlightForm, GateAssignmentForm
from .models import Flight, GateAssignment
from .forms import (FlightForm,FlightStatusUpdateForm,GateAssignmentForm,)
from .selectors import flights_visible_to
from django.utils import timezone
from .services import (InvalidFlightTransition,available_flight_status_choices,transition_flight_status,)
FLIGHT_MANAGEMENT_ROLES = (ADMIN,AIRLINE_OPERATOR,)

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
            "status_form": FlightStatusUpdateForm(flight=flight,),
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

    form = FlightStatusUpdateForm(
        request.POST,
        flight=flight,
    )

    if not form.is_valid():
        first_error = next(
            iter(form.errors.values()),
            ["Invalid flight status update."],
        )[0]

        messages.error(
            request,
            first_error,
        )

        return redirect(
            "flight_detail",
            id=flight.id,
        )

    try:
        flight = transition_flight_status(
            flight_id=flight.id,
            new_status=form.cleaned_data[
                "status"
            ],
            delay_minutes=(
                form.cleaned_data.get(
                    "delay_minutes"
                )
            ),
            reason=form.cleaned_data.get(
                "reason",
                "",
            ),
            actor=request.user,
            request=request,
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

            record_audit_event(
                action=AuditLog.Action.ASSIGN,
                instance=assignment,
                actor=request.user,
                request=request,
                description=(
                    f"Gate {assignment.gate.code} "
                    f"assigned to flight "
                    f"{flight.flight_number}."
                ),
                changes={
                    "gate": {
                        "from": None,
                        "to": assignment.gate.code,
                    },
                    "status": {
                        "from": None,
                        "to": assignment.status,
                    },
                },
            )

            messages.success(
                request,
                (
                    f"Gate {assignment.gate.code} "
                    f"assigned to "
                    f"{flight.flight_number}."
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
        previous_status = assignment.status
        gate_code = assignment.gate.code

        assignment.status = "RELEASED"
        assignment.released_time = timezone.now()
        assignment.save(
            update_fields=[
                "status",
                "released_time",
            ],
        )

        record_audit_event(
            action=AuditLog.Action.RELEASE,
            instance=assignment,
            actor=request.user,
            request=request,
            description=(
                f"Gate {gate_code} released "
                f"from flight "
                f"{assignment.flight.flight_number}."
            ),
            changes={
                "status": {
                    "from": previous_status,
                    "to": assignment.status,
                },
                "gate": {
                    "from": gate_code,
                    "to": None,
                },
            },
        )

        messages.success(
            request,
            (
                f"Gate {gate_code} "
                "released successfully."
            ),
        )
    else:
        messages.warning(
            request,
            "This gate assignment has already been released.",
        )

    return redirect(
        "flight_detail",
        id=assignment.flight_id,
    )
@require_GET
def public_flight_board(request):
    airports = Airport.objects.order_by(
        "city",
        "name",
    )

    requested_airport = request.GET.get(
        "airport",
        "",
    ).strip().upper()

    selected_airport = airports.filter(
        iata_code=requested_airport,
    ).first()

    if selected_airport is None:
        selected_airport = airports.first()

    return render(
        request,
        "flights/board.html",
        {
            "airports": airports,
            "selected_airport": selected_airport,
        },
    )

@require_GET
def public_flight_board_data(request):
    airport_code = request.GET.get(
        "airport",
        "",
    ).strip().upper()

    board_type = request.GET.get(
        "type",
        "DEPARTURES",
    ).strip().upper()

    if board_type not in {
        "ARRIVALS",
        "DEPARTURES",
    }:
        board_type = "DEPARTURES"

    airport = Airport.objects.filter(
        iata_code=airport_code,
    ).first()

    if airport is None:
        return JsonResponse(
            {
                "error": (
                    "A valid airport IATA "
                    "code is required."
                ),
            },
            status=400,
        )

    flights = public_board_flights(
        airport=airport,
        board_type=board_type,
    )

    rows = []

    for flight in flights:
        gate_assignment = next(
            iter(
                flight.active_gate_assignments
            ),
            None,
        )

        gate = (
            gate_assignment.gate.code
            if gate_assignment
            else None
        )

        terminal = (
            gate_assignment.gate.terminal.code
            if (
                gate_assignment
                and gate_assignment.gate.terminal
            )
            else None
        )

        if board_type == "ARRIVALS":
            scheduled_time = (
                flight.arrival_time
            )

            estimated_time = (
                flight.estimated_arrival_time
            )

            actual_time = (
                flight.actual_arrival_time
            )
        else:
            scheduled_time = (
                flight.departure_time
            )

            estimated_time = (
                flight.estimated_departure_time
            )

            actual_time = (
                flight.actual_departure_time
            )

        display_time = (
            actual_time
            or estimated_time
            or scheduled_time
        )

        delay_minutes = 0

        if estimated_time:
            delay_minutes = max(
                0,
                int(
                    (
                        estimated_time
                        - scheduled_time
                    ).total_seconds()
                    // 60
                ),
            )

        rows.append(
            {
                "id": flight.id,
                "flight_number": (
                    flight.flight_number
                ),
                "airline": {
                    "name": flight.airline.name,
                    "iata_code": (
                        flight.airline.iata_code
                    ),
                },
                "origin": {
                    "iata_code": (
                        flight.origin.iata_code
                    ),
                    "city": (
                        flight.origin.city
                    ),
                },
                "destination": {
                    "iata_code": (
                        flight.destination.iata_code
                    ),
                    "city": (
                        flight.destination.city
                    ),
                },
                "scheduled_time": (
                    scheduled_time.isoformat()
                ),
                "estimated_time": (
                    estimated_time.isoformat()
                    if estimated_time
                    else None
                ),
                "actual_time": (
                    actual_time.isoformat()
                    if actual_time
                    else None
                ),
                "display_time": (
                    display_time.isoformat()
                ),
                "delay_minutes": (
                    delay_minutes
                ),
                "disruption_reason": (
                    flight.disruption_reason
                ),
                "status": flight.status,
                "status_label": (
                    flight.get_status_display()
                ),
                "gate": gate,
                "terminal": terminal,
            }
        )

    return JsonResponse(
        {
            "airport": {
                "name": airport.name,
                "iata_code": (
                    airport.iata_code
                ),
                "city": airport.city,
            },
            "board_type": board_type,
            "updated_at": (
                timezone.now().isoformat()
            ),
            "count": len(rows),
            "flights": rows,
        }
    )