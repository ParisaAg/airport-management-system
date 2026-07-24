from django.shortcuts import render,redirect
from .models import Airline
from django.contrib.auth.decorators import login_required
from .forms import AirlineForm
from django.contrib import messages
from django.shortcuts import get_object_or_404

@login_required
def airline_create(request):


    if request.user.role != "ADMIN":

        return redirect(
            "airline_list"
        )



    if request.method == "POST":


        form = AirlineForm(
            request.POST
        )


        if form.is_valid():

            form.save()


            messages.success(
                request,
                "Airline created successfully"
            )


            return redirect(
                "airline_list"
            )


    else:


        form = AirlineForm()



    return render(
        request,
        "airlines/form.html",
        {
            "form":form,
            "title":"Create Airline"
        }
    )
@login_required
def airline_list(request):

    airlines = Airline.objects.all()

    return render(request,"airlines/list.html",{"airlines": airlines})


@login_required
def airline_edit(request, id):


    if request.user.role != "ADMIN":

        return redirect(
            "airline_list"
        )



    airline = get_object_or_404(Airline,id=id)



    if request.method == "POST":


        form = AirlineForm(request.POST,instance=airline)
        if form.is_valid():

            form.save()


            return redirect("airline_list")


    else:

        form = AirlineForm(instance=airline)

    return render(
        request,
        "airlines/form.html",
        {
            "form":form,
            "title":f"Edit {airline.name}"
        }
    )

@login_required
def airline_toggle_status(request, id):

    if request.user.role != "ADMIN":

        return redirect(
            "airline_list"
        )

    airline = get_object_or_404(Airline,id=id)

    airline.is_active = not airline.is_active
    airline.save()


    return redirect(
        "airline_list"
    )