from django.db.models.signals import pre_save
from django.dispatch import receiver
from operations.models import GroundOperation
from flights.models import Flight
from accounts.models import User
from .models import Notification
from flights.models import GateAssignment
from security.models import SecurityReport
from passenger_service.models import PassengerRequest



@receiver(pre_save, sender=Flight)
def flight_status_changed(sender, instance, **kwargs):

    if not instance.pk:
        return

    old_instance = sender.objects.get(pk=instance.pk)

    if (
        old_instance.status != 'DELAYED'
        and instance.status == 'DELAYED'
    ):

        admin_user = User.objects.filter(
            role='ADMIN'
        ).first()

        if admin_user:
            Notification.objects.create(
                user=admin_user,
                title="Flight Delayed",
                message=f"Flight {instance.flight_number} has been delayed.",
                notification_type="WARNING"
            )



@receiver(pre_save, sender=GroundOperation)
def ground_operation_completed(sender, instance, **kwargs):

    if not instance.pk:
        return

    old_instance = sender.objects.get(pk=instance.pk)

    if (
        old_instance.status != 'COMPLETED'
        and instance.status == 'COMPLETED'
    ):

        admin_user = User.objects.filter(
            role='ADMIN'
        ).first()

        if admin_user:
            Notification.objects.create(
                user=admin_user,
                title="Operation Completed",
                message=(
                    f"{instance.operation_type.name} "
                    f"operation for flight "
                    f"{instance.flight.flight_number} "
                    f"has been completed."
                ),
                notification_type="SUCCESS"
            )


@receiver(pre_save, sender=GateAssignment)
def gate_assignment_changed(sender, instance, **kwargs):

    if not instance.pk:
        return

    old_instance = sender.objects.get(pk=instance.pk)

    if old_instance.gate != instance.gate:

        admin_user = User.objects.filter(
            role='ADMIN'
        ).first()

        if admin_user:
            Notification.objects.create(
                user=admin_user,
                title="Gate Changed",
                message=(
                    f"Flight {instance.flight.flight_number} "
                    f"gate changed from "
                    f"{old_instance.gate.code} "
                    f"to {instance.gate.code}."
                ),
                notification_type="WARNING"
            )




@receiver(pre_save, sender=SecurityReport)
def critical_security_alert(sender, instance, **kwargs):

    if not instance.pk:
        return

    old_instance = sender.objects.get(pk=instance.pk)

    if (
        old_instance.severity != 'CRITICAL'
        and instance.severity == 'CRITICAL'
    ):

        admin_user = User.objects.filter(
            role='ADMIN'
        ).first()

        if admin_user:
            Notification.objects.create(
                user=admin_user,
                title="Critical Security Alert",
                message=(
                    f"Critical security issue reported "
                    f"for flight {instance.flight.flight_number}."
                ),
                notification_type="ERROR"
            )




@receiver(pre_save, sender=PassengerRequest)
def urgent_passenger_request(sender, instance, **kwargs):

    if not instance.pk:
        return

    old_instance = sender.objects.get(pk=instance.pk)

    if (
        old_instance.priority != 'URGENT'
        and instance.priority == 'URGENT'
    ):

        service_user = User.objects.filter(
            role='PASSENGER_SERVICE'
        ).first()

        if service_user:
            Notification.objects.create(
                user=service_user,
                title="Urgent Passenger Request",
                message=(
                    f"Urgent passenger request "
                    f"for flight "
                    f"{instance.flight.flight_number}."
                ),
                notification_type="WARNING"
            )