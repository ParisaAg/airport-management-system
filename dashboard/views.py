from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .services import DashboardService

@login_required
def dashboard_view(request):
    user = request.user
    airline_stats = None


    if user.role == "AIRLINE_OPERATOR":

        airline_stats = (
            DashboardService.airline_flight_statistics(
                user.airline
            )
        )
    context = {
        "role": user.role,
        "airline_stats": airline_stats,
        "flight_stats":
            DashboardService.flight_statistics(),

        "operation_stats":
            DashboardService.operation_statistics(),

        "security_stats":
            DashboardService.security_statistics(),

        "passenger_stats":
            DashboardService.passenger_statistics(),

    }


    return render(
        request,
        "dashboard/index.html",
        context
    )