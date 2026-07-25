from django.urls import path
from .views import aircraft_type_create, aircraft_type_edit, aircraft_type_list

urlpatterns = [
    path("types/",aircraft_type_list,name="aircraft_type_list"),
    path("types/create/",aircraft_type_create,name="aircraft_type_create"),
    path("types/edit/<int:id>/",aircraft_type_edit,name="aircraft_type_edit"),
]