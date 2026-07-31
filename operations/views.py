from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from accounts.permissions import (
    ADMIN,
    AIRPORT_MANAGER,
    GROUND_STAFF,
    role_required,
)
from flights.models import Flight

from .forms import GroundOperationForm, OperationTypeForm
from .models import GroundOperation, OperationType
from .services import (
    InvalidOperationTransition,
    transition_ground_operation,
)


MANAGEMENT_ROLES = (
    ADMIN,
    AIRPORT_MANAGER,
)

OPERATIONS_ROLES = (
    ADMIN,
    AIRPORT_MANAGER,
    GROUND_STAFF,
)


def operations_visible_to(user):
    queryset = (
        GroundOperation.objects
        .select_related(
            "flight",
            "operation_type",
            "assigned_staff",
        )
        .all()
    )

    if (
        user.is_superuser
        or user.role in MANAGEMENT_ROLES
    ):
        return queryset

    return queryset.filter(
        assigned_staff=user,
    )


@login_required
@role_required(*OPERATIONS_ROLES)
def operation_type_list(request):
    operation_types = OperationType.objects.all()

    return render(
        request,
        "operations/operation_types/list.html",
        {
            "operation_types": operation_types,
        },
    )


@login_required
@role_required(ADMIN)
def operation_type_create(request):
    if request.method == "POST":
        form = OperationTypeForm(request.POST)

        if form.is_valid():
            form.save()

            messages.success(
                request,
                "Operation type created successfully.",
            )

            return redirect("operation_type_list")
    else:
        form = OperationTypeForm()

    return render(
        request,
        "operations/operation_types/form.html",
        {
            "form": form,
            "title": "Create Operation Type",
        },
    )


@login_required
@role_required(ADMIN)
def operation_type_edit(request, id):
    operation_type = get_object_or_404(
        OperationType,
        id=id,
    )

    if request.method == "POST":
        form = OperationTypeForm(
            request.POST,
            instance=operation_type,
        )

        if form.is_valid():
            form.save()

            messages.success(
                request,
                "Operation type updated successfully.",
            )

            return redirect("operation_type_list")
    else:
        form = OperationTypeForm(
            instance=operation_type,
        )

    return render(
        request,
        "operations/operation_types/form.html",
        {
            "form": form,
            "title": "Edit Operation Type",
        },
    )


@login_required
@role_required(*OPERATIONS_ROLES)
def ground_operation_list(request):
    operations = operations_visible_to(
        request.user
    )

    status = request.GET.get("status")

    if status in dict(
        GroundOperation.STATUS_CHOICES
    ):
        operations = operations.filter(
            status=status,
        )

    return render(
        request,
        "operations/ground_operations/list.html",
        {
            "operations": operations,
            "statuses": GroundOperation.STATUS_CHOICES,
        },
    )


@login_required
@role_required(*MANAGEMENT_ROLES)
def ground_operation_create(request):
    if request.method == "POST":
        form = GroundOperationForm(request.POST)

        if form.is_valid():
            form.save()

            messages.success(
                request,
                "Ground operation created successfully.",
            )

            return redirect("ground_operation_list")
    else:
        form = GroundOperationForm()

    return render(
        request,
        "operations/ground_operations/form.html",
        {
            "form": form,
            "title": "Create Ground Operation",
        },
    )


@login_required
@role_required(*MANAGEMENT_ROLES)
def ground_operation_edit(request, id):
    operation = get_object_or_404(
        GroundOperation,
        id=id,
    )

    if request.method == "POST":
        form = GroundOperationForm(
            request.POST,
            instance=operation,
        )

        if form.is_valid():
            form.save()

            messages.success(
                request,
                "Ground operation updated successfully.",
            )

            return redirect("ground_operation_list")
    else:
        form = GroundOperationForm(
            instance=operation,
        )

    return render(
        request,
        "operations/ground_operations/form.html",
        {
            "form": form,
            "title": "Edit Ground Operation",
        },
    )


@login_required
@require_POST
@role_required(*OPERATIONS_ROLES)
def ground_operation_change_status(request, id):
    operation = get_object_or_404(
        operations_visible_to(request.user),
        id=id,
    )
    new_status = request.POST.get("status")
    try:
        transition_ground_operation(
            operation_id=operation.id,
            new_status=new_status,
        )
    except InvalidOperationTransition as error:
        messages.error(
            request,
            error.messages[0],
        )
    else:
        messages.success(request,"Operation status updated successfully.",)
    return redirect("ground_operation_list")

@login_required
@role_required(*MANAGEMENT_ROLES)
def ground_operation_create_for_flight(
    request,
    flight_id,
):
    flight = get_object_or_404(
        Flight,
        id=flight_id,
    )

    if request.method == "POST":
        form = GroundOperationForm(
            request.POST,
        )

        if form.is_valid():
            operation = form.save(
                commit=False,
            )

            operation.flight = flight
            operation.save()

            messages.success(
                request,
                "Ground operation added to flight.",
            )

            return redirect(
                "flight_detail",
                id=flight.id,
            )
    else:
        form = GroundOperationForm(
            initial={"flight": flight},
        )

        form.fields["flight"].widget = (
            form.fields["flight"].hidden_widget()
        )
    return render(
        request,"operations/ground_operations/form.html",{"form": form,"title": "Create Ground Operation","flight": flight,},)