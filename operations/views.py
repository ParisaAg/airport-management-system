from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import OperationType
from .forms import OperationTypeForm



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