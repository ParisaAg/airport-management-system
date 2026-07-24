from django.shortcuts import render
from .models import Notification
from django.shortcuts import get_object_or_404, redirect
from django.db.models import Q


def notification_list(request):

    user = request.user


    if user.role == 'ADMIN':

        notifications = Notification.objects.all()


    elif user.role == 'SECURITY_OFFICER':

        notifications = Notification.objects.filter(
            Q(title__icontains='Security')
            |
            Q(notification_type='ERROR')
        )


    elif user.role == 'GROUND_STAFF':

        notifications = Notification.objects.filter(
            title__icontains='Operation'
        )


    elif user.role == 'PASSENGER_SERVICE':

        notifications = Notification.objects.filter(
            title__icontains='Passenger'
        )


    else:

        notifications = Notification.objects.filter(
            user=user
        )


    notifications = notifications.order_by(
        '-created_at'
    )


    return render(
        request,
        'notifications/list.html',
        {
            'notifications': notifications
        }
    )



def mark_as_read(request, pk):

    notification = get_object_or_404(
        Notification,
        id=pk,
        user=request.user
    )


    notification.is_read = True

    notification.save()


    return redirect(
        'notifications'
    )