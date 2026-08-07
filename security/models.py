from django.conf import settings
from django.db import models
from django.utils import timezone


class SecurityReport(models.Model):
    REPORT_TYPE_CHOICES = (
        ("PASSENGER", "Passenger Issue"),
        ("BAGGAGE", "Baggage Issue"),
        ("AIRCRAFT", "Aircraft Security"),
        ("ACCESS", "Access Control"),
        ("OTHER", "Other"),
    )

    SEVERITY_CHOICES = (
        ("LOW", "Low"),
        ("MEDIUM", "Medium"),
        ("HIGH", "High"),
        ("CRITICAL", "Critical"),
    )

    STATUS_CHOICES = (
        ("OPEN", "Open"),
        (
            "INVESTIGATING",
            "Investigating",
        ),
        ("RESOLVED", "Resolved"),
        ("CLOSED", "Closed"),
    )

    flight = models.ForeignKey(
        "flights.Flight",
        on_delete=models.PROTECT,
        related_name="security_reports",
        verbose_name="Flight",
    )

    officer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="security_reports",
        verbose_name="Security Officer",
    )

    report_type = models.CharField(
        max_length=20,
        choices=REPORT_TYPE_CHOICES,
        verbose_name="Report Type",
    )

    severity = models.CharField(
        max_length=20,
        choices=SEVERITY_CHOICES,
        default="LOW",
        verbose_name="Severity",
    )

    description = models.TextField(
        verbose_name="Description",
    )

    location = models.CharField(
        max_length=150,
        blank=True,
        verbose_name="Incident Location",
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="OPEN",
        db_index=True,
        verbose_name="Status",
    )

    resolution_notes = models.TextField(
        blank=True,
        verbose_name="Resolution Notes",
    )

    resolved_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Resolved At",
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
        verbose_name = "Security Report"

        verbose_name_plural = (
            "Security Reports"
        )

        ordering = [
            "-created_at",
        ]

        indexes = [
            models.Index(
                fields=[
                    "status",
                    "severity",
                ],
                name="security_status_severity",
            ),
            models.Index(
                fields=[
                    "flight",
                    "status",
                ],
                name="security_flight_status",
            ),
            models.Index(
                fields=[
                    "officer",
                    "status",
                ],
                name="security_officer_status",
            ),
        ]

    @property
    def reference(self):
        if not self.pk:
            return "SEC-NEW"

        return f"SEC-{self.pk:06d}"

    @property
    def is_active(self):
        return self.status in {
            "OPEN",
            "INVESTIGATING",
        }

    def __str__(self):
        reference = (
            self.reference
            if self.pk
            else "Security Report"
        )

        return (
            f"{reference} - "
            f"{self.flight.flight_number} - "
            f"{self.get_report_type_display()}"
        )