from django.urls import path

from .views import (
    ground_operation_change_status,
    ground_operation_create_for_flight,
    ground_operation_edit,
    operation_type_list,
    operation_type_create,
    operation_type_edit,
    ground_operation_list,
    ground_operation_create

)



urlpatterns = [

    path("types/",operation_type_list,name="operation_type_list"),
    path("types/create/",operation_type_create,name="operation_type_create"),
    path("types/edit/<int:id>/",operation_type_edit,name="operation_type_edit"),
    path("ground-operations/",ground_operation_list,name="ground_operation_list"),
    path("ground-operations/create/",ground_operation_create,name="ground_operation_create"),
    path("operations/edit/<int:id>/",ground_operation_edit,name="ground_operation_edit"),
    path("operations/status/<int:id>/",ground_operation_change_status,name="ground_operation_change_status"),
    path("flight/<int:flight_id>/operation/create/",ground_operation_create_for_flight,name="ground_operation_create_for_flight"),
]