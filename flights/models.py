from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone


class Flight(models.Model):
    STATUS_CHOICES = (
        ("SCHEDULED", "Scheduled"),
        ("BOARDING", "Boarding"),
        ("DEPARTED", "Departed"),
        ("ARRIVED", "Arrived"),
        ("DELAYED", "Delayed"),
        ("CANCELLED", "Cancelled"),
    )

    flight_number = models.CharField(max_length=10,unique=True,db_index=True,verbose_name="Flight Number",)
    airline = models.ForeignKey("airlines.Airline",on_delete=models.PROTECT,related_name="flights",verbose_name="Airline",)
    aircraft = models.ForeignKey("fleet.Aircraft",on_delete=models.PROTECT,related_name="flights",verbose_name="Aircraft",)
    origin = models.ForeignKey("airports.Airport",on_delete=models.PROTECT,related_name="departing_flights", verbose_name="Origin Airport",)
    destination = models.ForeignKey("airports.Airport", on_delete=models.PROTECT,related_name="arriving_flights",verbose_name="Destination Airport",)
    departure_time = models.DateTimeField(verbose_name="Departure Time",)
    arrival_time = models.DateTimeField(verbose_name="Arrival Time",)
    status = models.CharField(max_length=20,choices=STATUS_CHOICES,default="SCHEDULED",verbose_name="Flight Status",)

    estimated_departure_time = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Estimated Departure Time",
    )

    estimated_arrival_time = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Estimated Arrival Time",
    )

    actual_departure_time = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Actual Departure Time",
    )

    actual_arrival_time = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Actual Arrival Time",
    )

    disruption_reason = models.TextField(
        blank=True,
        verbose_name="Delay or Cancellation Reason",
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
        verbose_name = "Flight"
        verbose_name_plural = "Flights"
        ordering = ["departure_time"]

        indexes = [
            models.Index(
                fields=[
                    "origin",
                    "departure_time",
                    "status",
                ],
                name="flight_departure_board",
            ),
            models.Index(
                fields=[
                    "destination",
                    "arrival_time",
                    "status",
                ],
                name="flight_arrival_board",
            ),
        ]

    def clean(self):
        super().clean()

        if (
            self.origin_id
            and self.destination_id
            and self.origin_id == self.destination_id
        ):
            raise ValidationError(
                (
                    "Origin airport and destination "
                    "airport cannot be the same."
                )
            )

        if (
            self.departure_time
            and self.arrival_time
            and self.arrival_time <= self.departure_time
        ):
            raise ValidationError(
                (
                    "Arrival time must be after "
                    "departure time."
                )
            )

        if (
            self.estimated_departure_time
            and self.estimated_arrival_time
            and (
                self.estimated_arrival_time
                <= self.estimated_departure_time
            )
        ):
            raise ValidationError(
                {
                    "estimated_arrival_time": (
                        "Estimated arrival time must be "
                        "after estimated departure time."
                    )
                }
            )

        if (
            self.estimated_departure_time
            and self.departure_time
            and (
                self.estimated_departure_time
                < self.departure_time
            )
        ):
            raise ValidationError(
                {
                    "estimated_departure_time": (
                        "Estimated departure cannot be "
                        "before scheduled departure."
                    )
                }
            )

        if (
            self.actual_departure_time
            and self.actual_arrival_time
            and (
                self.actual_arrival_time
                < self.actual_departure_time
            )
        ):
            raise ValidationError(
                {
                    "actual_arrival_time": (
                        "Actual arrival time cannot be "
                        "before actual departure time."
                    )
                }
            )

    def __str__(self):
        return (
            f"{self.flight_number} - "
            f"{self.origin.iata_code} to "
            f"{self.destination.iata_code}"
        )


class GateAssignment(models.Model):
    STATUS_CHOICES = (
        ("ACTIVE", "Active"),
        ("RELEASED", "Released"),
        ("CANCELLED", "Cancelled"),
    )

    flight = models.ForeignKey(
        Flight,
        on_delete=models.PROTECT,
        related_name="gate_assignments",
        verbose_name="Flight",
    )

    gate = models.ForeignKey(
        "airports.Gate",
        on_delete=models.PROTECT,
        related_name="assignments",
        verbose_name="Gate",
    )

    assigned_time = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Assigned Time",
    )

    released_time = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name="Released Time",
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="ACTIVE",
        verbose_name="Status",
    )

    notes = models.TextField(
        blank=True,
        null=True,
        verbose_name="Notes",
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    class Meta:
        verbose_name = "Gate Assignment"
        verbose_name_plural = "Gate Assignments"
        ordering = ["-assigned_time"]

    def clean(self):
        super().clean()

        if (
            self.released_time
            and self.assigned_time
            and self.released_time < self.assigned_time
        ):
            raise ValidationError(
                {
                    "released_time": (
                        "Released time cannot be "
                        "before assigned time."
                    )
                }
            )

        if (
            self.status == "RELEASED"
            and not self.released_time
        ):
            raise ValidationError(
                {
                    "released_time": (
                        "Released assignments must "
                        "have a released time."
                    )
                }
            )

        if self.gate_id:
            conflicts = (
                GateAssignment.objects
                .filter(
                    gate_id=self.gate_id,
                    status="ACTIVE",
                )
                .exclude(pk=self.pk)
            )

            if conflicts.exists():
                raise ValidationError(
                    {
                        "gate": (
                            "This gate already has an "
                            "active flight assignment."
                        )
                    }
                )

    def __str__(self):
        return (
            f"{self.flight.flight_number} - "
            f"{self.gate.code}"
        )