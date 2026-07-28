from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .services import DashboardService
from notifications.models import Notification
from flights.models import Flight
from operations.models import GroundOperation

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



    # =========================
    # Recent Activity
    # =========================

    recent_notifications = Notification.objects.filter(user=user).order_by("-created_at")[:1]
    recent_flights = Flight.objects.all().order_by("-created_at")[:1]
    recent_operations = GroundOperation.objects.all().order_by("-created_at")[:1]

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
        # Activity
        "recent_notifications":
            recent_notifications,
        "recent_flights":
            recent_flights,
        "recent_operations":
            recent_operations,

    }

    return render(request,"dashboard/index.html",context)

def landing_page(request):

    return render(request,"landing.html")