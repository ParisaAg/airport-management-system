from django.urls import path
from .views import aircraft_type_create, aircraft_type_edit, aircraft_type_list
from .views import aircraft_list, aircraft_create
from .views import aircraft_edit, aircraft_change_status



urlpatterns = [
    path("types/",aircraft_type_list,name="aircraft_type_list"),
    path("types/create/",aircraft_type_create,name="aircraft_type_create"),
    path("types/edit/<int:id>/",aircraft_type_edit,name="aircraft_type_edit"),
    path("aircrafts/",aircraft_list,name="aircraft_list"),
    path("aircrafts/create/",aircraft_create,name="aircraft_create"),
    path("aircrafts/edit/<int:id>/",aircraft_edit,name="aircraft_edit"),
    path("aircrafts/status/<int:id>/",aircraft_change_status,name="aircraft_change_status"),
]