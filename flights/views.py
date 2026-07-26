from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .models import Flight
from django.shortcuts import redirect
from .forms import FlightForm
from django.contrib import messages
from django.shortcuts import get_object_or_404


@login_required
def flight_list(request):

    flights = Flight.objects.all()


    search = request.GET.get("search")


    status = request.GET.get("status")



    if search:

        flights = flights.filter(
            flight_number__icontains=search
        )



    if status:

        flights = flights.filter(
            status=status
        )



    return render(request,"flights/list.html",{"flights": flights,"statuses": Flight.STATUS_CHOICES})


@login_required
def flight_create(request):


    if request.user.role not in [
        "ADMIN",
        "AIRLINE_OPERATOR"
    ]:

        return redirect("flight_list")



    if request.method == "POST":

        form = FlightForm(
            request.POST,
            user=request.user
        )


        if form.is_valid():

            flight = form.save(
                commit=False
            )


            if request.user.role == "AIRLINE_OPERATOR":
                flight.airline = request.user.airline
            flight.save()

            return redirect(
                "flight_list"
            )


    else:

        form = FlightForm(
            user=request.user
        )

    return render(request,"flights/create.html",{"form":form})


@login_required
def flight_edit(request, id):


    flight = get_object_or_404(
        Flight,
        id=id
    )


    if request.user.role == "AIRLINE_OPERATOR":


        if flight.airline != request.user.airline:

            return redirect(
                "flight_list"
            )



    if request.user.role not in [
        "ADMIN",
        "AIRLINE_OPERATOR"
    ]:
        return redirect(
            "flight_list"
        )

    if request.method == "POST":
        form = FlightForm(request.POST,instance=flight,user=request.user)

        if form.is_valid():
            form.save()
            return redirect(
                "flight_list"
            )

    else:
        form = FlightForm(instance=flight,user=request.user)



    return render(request,"flights/create.html",{"form":form,"edit":True})


@login_required
def flight_delete(request, id):

    flight = get_object_or_404(
        Flight,
        id=id
    )

    if request.user.role != "ADMIN":

        return redirect("flight_list")

    if request.method == "POST":
        flight.delete()

        return redirect("flight_list")



    return render(request,"flights/delete.html",{"flight":flight})

@login_required
def flight_detail(request, id):
    flight = get_object_or_404(
        Flight,
        id=id
    )
    return render(request,"flights/detail.html",{"flight": flight})



@login_required
def flight_change_status(request, id):


    flight = get_object_or_404(
        Flight,
        id=id
    )


    if request.user.role != "ADMIN":

        return redirect(
            "flight_detail",
            id=id
        )


    if request.method == "POST":

        new_status = request.POST.get(
            "status"
        )


        if new_status in dict(
            Flight.STATUS_CHOICES
        ):

            flight.status = new_status

            flight.save()



    return render(
        request,
        "flights/detail.html",
        {
            "flight": flight,
            "statuses": Flight.STATUS_CHOICES
        }
    )