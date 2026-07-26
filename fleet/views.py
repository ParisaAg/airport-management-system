from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .models import AircraftType, Aircraft
from django.shortcuts import redirect
from django.contrib import messages
from .forms import AircraftTypeForm
from django.shortcuts import get_object_or_404
from .forms import AircraftForm
@login_required
def aircraft_type_list(request):

    aircraft_types = AircraftType.objects.all()


    return render(
        request,
        "fleet/aircraft_types/list.html",
        {
            "aircraft_types": aircraft_types
        }
    )


@login_required
def aircraft_type_create(request):


    if request.user.role != "ADMIN":

        return redirect(
            "aircraft_type_list"
        )



    if request.method == "POST":


        form = AircraftTypeForm(
            request.POST
        )


        if form.is_valid():

            form.save()


            messages.success(
                request,
                "Aircraft type created successfully"
            )


            return redirect(
                "aircraft_type_list"
            )


    else:


        form = AircraftTypeForm()



    return render(
        request,
        "fleet/aircraft_types/form.html",
        {
            "form": form,
            "title": "Create Aircraft Type"
        }
    )


@login_required
def aircraft_type_edit(request, id):


    if request.user.role != "ADMIN":

        return redirect(
            "aircraft_type_list"
        )



    aircraft_type = get_object_or_404(
        AircraftType,
        id=id
    )



    if request.method == "POST":


        form = AircraftTypeForm(
            request.POST,
            instance=aircraft_type
        )


        if form.is_valid():

            form.save()


            return redirect(
                "aircraft_type_list"
            )


    else:


        form = AircraftTypeForm(
            instance=aircraft_type
        )



    return render(
        request,
        "fleet/aircraft_types/form.html",
        {
            "form": form,
            "title": f"Edit {aircraft_type}"
        }
    )

@login_required
def aircraft_list(request):

    aircrafts = Aircraft.objects.select_related(
        "airline",
        "aircraft_type"
    ).all()


    return render(
        request,
        "fleet/aircrafts/list.html",
        {
            "aircrafts": aircrafts
        }
    )


@login_required
def aircraft_create(request):


    if request.user.role != "ADMIN":

        return redirect(
            "aircraft_list"
        )



    if request.method == "POST":


        form = AircraftForm(
            request.POST
        )


        if form.is_valid():

            form.save()


            return redirect(
                "aircraft_list"
            )



    else:


        form = AircraftForm()



    return render(request,"fleet/aircrafts/form.html",{"form": form,"title": "Create Aircraft"})


@login_required
def aircraft_edit(request, id):


    if request.user.role != "ADMIN":

        return redirect(
            "aircraft_list"
        )



    aircraft = get_object_or_404(
        Aircraft,
        id=id
    )



    if request.method == "POST":


        form = AircraftForm(
            request.POST,
            instance=aircraft
        )


        if form.is_valid():

            form.save()


            return redirect(
                "aircraft_list"
            )



    else:


        form = AircraftForm(
            instance=aircraft
        )



    return render(
        request,
        "fleet/aircrafts/form.html",
        {
            "form": form,
            "title": f"Edit {aircraft.registration_number}"
        }
    )



@login_required
def aircraft_change_status(request, id):


    if request.user.role != "ADMIN":

        return redirect(
            "aircraft_list"
        )


    aircraft = get_object_or_404(
        Aircraft,
        id=id
    )


    if aircraft.status == "ACTIVE":

        aircraft.status = "MAINTENANCE"

    elif aircraft.status == "MAINTENANCE":

        aircraft.status = "RETIRED"

    else:

        aircraft.status = "ACTIVE"



    aircraft.save()


    return redirect(
        "aircraft_list"
    )