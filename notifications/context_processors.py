from .models import Notification


def notification_count(request):

    if not request.user.is_authenticated:
        return {}


    notifications = Notification.objects.filter(
        user=request.user
    ).order_by(
        '-created_at'
    )


    return {

        "unread_notifications_count":
            notifications.filter(
                is_read=False
            ).count(),


        "latest_notifications":
            notifications[:5]

    }