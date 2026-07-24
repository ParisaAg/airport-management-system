from django.urls import path

from .views import mark_as_read, notification_list


urlpatterns = [

    path('',notification_list,name='notifications'),
    path('read/<int:pk>/',mark_as_read,name='mark_as_read'),

]