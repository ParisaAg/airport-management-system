from django.urls import path
from .views import flight_change_status, flight_create, flight_detail, flight_list,flight_edit,flight_delete, gate_assignment_create, gate_assignment_release, public_flight_board, public_flight_board_data
public_flight_board_data,public_flight_board



urlpatterns = [
    path("",flight_list,name="flight_list"),
    path("create/",flight_create,name="flight_create"),
    path("edit/<int:id>/",flight_edit,name="flight_edit"),
    path("delete/<int:id>/",flight_delete,name="flight_delete"),
    path("<int:id>/",flight_detail,name="flight_detail"),
    path("change-status/<int:id>/",flight_change_status,name="flight_change_status"),
    path("gate-assignment/<int:id>/",gate_assignment_create,name="gate_assignment_create"),
    path("gate-release/<int:id>/",gate_assignment_release,name="gate_assignment_release"),
    path("board/",public_flight_board,name="public_flight_board",),
    path("board/data/",public_flight_board_data,name="public_flight_board_data"),
]