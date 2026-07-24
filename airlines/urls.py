from django.urls import path
from .views import airline_create, airline_list,airline_edit, airline_toggle_status



urlpatterns = [

    path("",airline_list,name="airline_list"),
    path("create/",airline_create,name="airline_create"),
    path("edit/<int:id>/",airline_edit,name="airline_edit"),
    path("toggle-status/<int:id>/",airline_toggle_status,name="airline_toggle_status"),
]