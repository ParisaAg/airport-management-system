from django.conf import settings
from django.db import models
from django.utils import timezone


class PassengerRequest(models.Model):

    REQUEST_TYPE_CHOICES = (
        (
            "WHEELCHAIR",
            "Wheelchair Assistance",
        ),
        (
            "LOST_FOUND",
            "Lost and Found",
        ),
        (
            "SPECIAL_ASSISTANCE",
            "Special Assistance",
        ),
        (
            "COMPLAINT",
            "Complaint",
        ),
        (
            "OTHER",
            "Other",
        ),
    )

    PRIORITY_CHOICES = (
        ("LOW", "Low"),
        ("MEDIUM", "Medium"),
        ("HIGH", "High"),
        ("URGENT", "Urgent"),
    )

    STATUS_CHOICES = (
        ("OPEN", "Open"),
        ("ASSIGNED", "Assigned"),
        ("IN_PROGRESS", "In Progress"),
        ("COMPLETED", "Completed"),
        ("CANCELLED", "Cancelled"),
    )

    flight = models.ForeignKey(
        "flights.Flight",
        on_delete=models.PROTECT,
        related_name="passenger_requests",
        verbose_name="Flight",
    )

    passenger_name = models.CharField(
        max_length=100,
        verbose_name="Passenger Name",
    )

    booking_reference = models.CharField(
        max_length=30,
        blank=True,
        verbose_name="Booking Reference",
    )

    request_type = models.CharField(
        max_length=30,
        choices=REQUEST_TYPE_CHOICES,
        verbose_name="Request Type",
    )

    priority = models.CharField(
        max_length=20,
        choices=PRIORITY_CHOICES,
        default="LOW",
        db_index=True,
        verbose_name="Priority",
    )

    service_location = models.CharField(
        max_length=150,
        blank=True,
        verbose_name="Service Location",
    )

    description = models.TextField(
        verbose_name="Description",
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="OPEN",
        db_index=True,
        verbose_name="Status",
    )

    assigned_staff = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="passenger_requests",
        verbose_name="Assigned Staff",
    )

    resolution_notes = models.TextField(
        blank=True,
        verbose_name="Resolution Notes",
    )

    completed_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Completed At",
    )

    status_updated_at = models.DateTimeField(
        default=timezone.now,
        verbose_name="Status Updated At",
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        verbose_name = "Passenger Request"
        verbose_name_plural = "Passenger Requests"

        ordering = [
            "-created_at",
        ]

        indexes = [
            models.Index(
                fields=[
                    "status",
                    "priority",
                ],
                name="passenger_status_priority",
            ),
            models.Index(
                fields=[
                    "flight",
                    "status",
                ],
                name="passenger_flight_status",
            ),
            models.Index(
                fields=[
                    "assigned_staff",
                    "status",
                ],
                name="passenger_staff_status",
            ),
        ]

    @property
    def reference(self):
        if not self.pk:
            return "PSR-NEW"

        return f"PSR-{self.pk:06d}"

    @property
    def is_active(self):
        return self.status in {
            "OPEN",
            "ASSIGNED",
            "IN_PROGRESS",
        }

    def __str__(self):
        return (
            f"{self.reference} - "
            f"{self.passenger_name}"
        )