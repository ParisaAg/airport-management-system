from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from accounts.permissions import ADMIN, role_required

from .forms import AirlineForm
from .models import Airline


@login_required
def airline_list(request):
    airlines = Airline.objects.all()

    return render(
        request,
        "airlines/list.html",
        {"airlines": airlines},
    )


@login_required
@role_required(ADMIN)
def airline_create(request):
    if request.method == "POST":
        form = AirlineForm(request.POST)

        if form.is_valid():
            form.save()

            messages.success(
                request,
                "Airline created successfully.",
            )

            return redirect("airline_list")
    else:
        form = AirlineForm()

    return render(
        request,
        "airlines/form.html",
        {
            "form": form,
            "title": "Create Airline",
        },
    )


@login_required
@role_required(ADMIN)
def airline_edit(request, id):
    airline = get_object_or_404(
        Airline,
        id=id,
    )

    if request.method == "POST":
        form = AirlineForm(
            request.POST,
            instance=airline,
        )

        if form.is_valid():
            form.save()

            messages.success(
                request,
                "Airline updated successfully.",
            )

            return redirect("airline_list")
    else:
        form = AirlineForm(instance=airline)

    return render(
        request,
        "airlines/form.html",
        {
            "form": form,
            "title": f"Edit {airline.name}",
        },
    )


@login_required
@require_POST
@role_required(ADMIN)
def airline_toggle_status(request, id):
    airline = get_object_or_404(
        Airline,
        id=id,
    )

    airline.is_active = not airline.is_active
    airline.save(update_fields=["is_active"])

    status_text = (
        "activated"
        if airline.is_active
        else "deactivated"
    )

    messages.success(
        request,
        f"{airline.name} {status_text} successfully.",
    )

    return redirect("airline_list")