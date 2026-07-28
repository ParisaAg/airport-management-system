from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .forms import OperationTypeForm
from .models import OperationType, GroundOperation
from .forms import OperationTypeForm, GroundOperationForm
from flights.models import Flight


@login_required
def operation_type_list(request):
    operation_types = OperationType.objects.all()

    return render(request,"operations/operation_types/list.html",{"operation_types": operation_types})
@login_required
def operation_type_create(request):


    if request.user.role != "ADMIN":
        return redirect("operation_type_list")

    if request.method == "POST":
        form = OperationTypeForm(
            request.POST
        )
        if form.is_valid():
            form.save()
            return redirect("operation_type_list")
    else:
        form = OperationTypeForm()
    return render(request,"operations/operation_types/form.html",{"form": form,"title": "Create Operation Type"})

@login_required
def operation_type_edit(request, id):
    if request.user.role != "ADMIN":
        return redirect("operation_type_list")

    operation_type = get_object_or_404(OperationType,id=id)
    if request.method == "POST":
        form = OperationTypeForm(request.POST,instance=operation_type)
        if form.is_valid():
            form.save()
            return redirect("operation_type_list")
    else:
        form = OperationTypeForm(instance=operation_type)
    return render(request,"operations/operation_types/form.html",
        {"form": form,"title": "Edit Operation Type"})

@login_required
def ground_operation_list(request):
    operations = GroundOperation.objects.all()
    return render(
        request,"operations/ground_operations/list.html",{ "operations": operations})

@login_required
def ground_operation_create(request):

    if request.user.role not in [
        "ADMIN",
        "GROUND_STAFF"
    ]:

        return redirect(
            "ground_operation_list"
        )

    if request.method == "POST":
        form = GroundOperationForm(
            request.POST
        )
        if form.is_valid():
            form.save()
            return redirect("ground_operation_list")
    else:
        form = GroundOperationForm()
    return render(request,"operations/ground_operations/form.html",{"form": form,"title": "Create Ground Operation"})




@login_required
def ground_operation_edit(request, id):
    if request.user.role not in [
        "ADMIN",
        "GROUND_STAFF"
    ]:
        return redirect("ground_operation_list")

    operation = get_object_or_404(
        GroundOperation,
        id=id
    )

    if request.method == "POST":
        form = GroundOperationForm(
            request.POST,
            instance=operation
        )
        if form.is_valid():

            form.save()
            return redirect(
                "ground_operation_list"
            )

    else:
        form = GroundOperationForm(
            instance=operation
        )
    return render(request,"operations/ground_operations/form.html",{"form": form,"title": "Edit Ground Operation"})

@login_required
def ground_operation_change_status(request, id):


    if request.user.role not in [
        "ADMIN",
        "GROUND_STAFF"
    ]:

        return redirect(
            "ground_operation_list"
        )

    operation = get_object_or_404(GroundOperation,id=id)
    if request.method == "POST":
        status = request.POST.get(
            "status"
        )
        if status in dict(
            GroundOperation.STATUS_CHOICES
        ):
            operation.status = status
            if status == "COMPLETED":
                from django.utils import timezone
                operation.end_time = timezone.now()
            operation.save()
    return redirect("ground_operation_list")




@login_required
def ground_operation_create_for_flight(request, flight_id):
    if request.user.role not in [
        "ADMIN",
        "GROUND_STAFF"
    ]:

        return redirect(
            "flight_detail",
            id=flight_id
        )

    flight = get_object_or_404(
        Flight,
        id=flight_id
    )

    if request.method == "POST":
        form = GroundOperationForm(
            request.POST
        )

        if form.is_valid():

            operation = form.save(
                commit=False
            )
            operation.flight = flight
            operation.save()

            return redirect(
                "flight_detail",
                id=flight.id
            )
    else:
        form = GroundOperationForm()
    return render(request,"operations/ground_operations/form.html",{"form": form,"title": "Create Ground Operation","flight": flight})