from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from accounts.permissions import ADMIN, role_required

from .forms import AircraftForm, AircraftTypeForm
from .models import Aircraft, AircraftType


@login_required
def aircraft_type_list(request):
    aircraft_types = AircraftType.objects.all()

    return render(
        request,
        "fleet/aircraft_types/list.html",
        {"aircraft_types": aircraft_types},
    )


@login_required
@role_required(ADMIN)
def aircraft_type_create(request):
    if request.method == "POST":
        form = AircraftTypeForm(request.POST)

        if form.is_valid():
            form.save()

            messages.success(
                request,
                "Aircraft type created successfully.",
            )

            return redirect("aircraft_type_list")
    else:
        form = AircraftTypeForm()

    return render(
        request,
        "fleet/aircraft_types/form.html",
        {
            "form": form,
            "title": "Create Aircraft Type",
        },
    )


@login_required
@role_required(ADMIN)
def aircraft_type_edit(request, id):
    aircraft_type = get_object_or_404(
        AircraftType,
        id=id,
    )

    if request.method == "POST":
        form = AircraftTypeForm(
            request.POST,
            instance=aircraft_type,
        )

        if form.is_valid():
            form.save()

            messages.success(
                request,
                "Aircraft type updated successfully.",
            )

            return redirect("aircraft_type_list")
    else:
        form = AircraftTypeForm(
            instance=aircraft_type,
        )

    return render(
        request,
        "fleet/aircraft_types/form.html",
        {
            "form": form,
            "title": f"Edit {aircraft_type}",
        },
    )


@login_required
def aircraft_list(request):
    aircrafts = (
        Aircraft.objects
        .select_related(
            "airline",
            "aircraft_type",
        )
        .all()
    )

    return render(
        request,
        "fleet/aircrafts/list.html",
        {"aircrafts": aircrafts},
    )


@login_required
@role_required(ADMIN)
def aircraft_create(request):
    if request.method == "POST":
        form = AircraftForm(request.POST)

        if form.is_valid():
            form.save()

            messages.success(
                request,
                "Aircraft created successfully.",
            )

            return redirect("aircraft_list")
    else:
        form = AircraftForm()

    return render(
        request,
        "fleet/aircrafts/form.html",
        {
            "form": form,
            "title": "Create Aircraft",
        },
    )


@login_required
@role_required(ADMIN)
def aircraft_edit(request, id):
    aircraft = get_object_or_404(
        Aircraft,
        id=id,
    )

    if request.method == "POST":
        form = AircraftForm(
            request.POST,
            instance=aircraft,
        )

        if form.is_valid():
            form.save()

            messages.success(
                request,
                "Aircraft updated successfully.",
            )

            return redirect("aircraft_list")
    else:
        form = AircraftForm(instance=aircraft)

    return render(
        request,
        "fleet/aircrafts/form.html",
        {
            "form": form,
            "title": (
                f"Edit {aircraft.registration_number}"
            ),
        },
    )


@login_required
@require_POST
@role_required(ADMIN)
def aircraft_change_status(request, id):
    aircraft = get_object_or_404(
        Aircraft,
        id=id,
    )

    status_flow = {
        "ACTIVE": "MAINTENANCE",
        "MAINTENANCE": "RETIRED",
        "RETIRED": "ACTIVE",
    }

    aircraft.status = status_flow[aircraft.status]
    aircraft.save(update_fields=["status"])

    messages.success(
        request,
        (
            f"{aircraft.registration_number} status "
            f"changed to {aircraft.get_status_display()}."
        ),
    )

    return redirect("aircraft_list")