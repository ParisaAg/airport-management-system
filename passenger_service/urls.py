from django.urls import path

from . import views


app_name = "passenger_service"


urlpatterns = [
    path("",views.passenger_request_list,name="list",),
    path("create/",views.passenger_request_create,name="create",),
    path("<int:id>/",views.passenger_request_detail,name="detail",),
    path("<int:id>/assign/",views.passenger_request_assign,name="assign",),
    path("<int:id>/status/",views.passenger_request_change_status,name="change_status",),
]