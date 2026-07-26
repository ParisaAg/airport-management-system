from django.urls import path

from .views import (
    operation_type_list,
    operation_type_create,
    operation_type_edit,
)



urlpatterns = [

    path("types/",operation_type_list,name="operation_type_list"),
    path("types/create/",operation_type_create,name="operation_type_create"),
    path("types/edit/<int:id>/",operation_type_edit,name="operation_type_edit"),
]