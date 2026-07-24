from django.urls import path
from .views import flight_create, flight_list,flight_edit,flight_delete



urlpatterns = [
    path("",flight_list,name="flight_list"),
    path("create/",flight_create,name="flight_create"),
    path("edit/<int:id>/",flight_edit,name="flight_edit"),
    path("delete/<int:id>/",flight_delete,name="flight_delete"),
]