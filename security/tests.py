from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

from airlines.models import Airline
from airports.models import Airport
from audit.models import AuditLog
from fleet.models import (
    Aircraft,
    AircraftType,
)
from flights.models import Flight

from .models import SecurityReport
from .services import (
    InvalidSecurityAssignment,
    InvalidSecurityTransition,
    assign_security_officer,
    available_security_status_choices,
    transition_security_report_status,
)


User = get_user_model()


class SecurityWorkflowTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.airline = Airline.objects.create(
            name="Security Test Air",
            iata_code="ST",
            icao_code="STA",
            country="Iran",
        )

        cls.aircraft_type = (
            AircraftType.objects.create(
                manufacturer="Airbus",
                model="A320-SEC",
                passenger_capacity=180,
                range_km=6100,
            )
        )

        cls.aircraft = Aircraft.objects.create(
            airline=cls.airline,
            aircraft_type=cls.aircraft_type,
            registration_number="EP-SEC",
            serial_number="SEC-001",
            manufacture_year=2020,
        )

        cls.origin = Airport.objects.create(
            name="Security Origin Airport",
            icao_code="OISA",
            iata_code="SOA",
            country="Iran",
            city="Tehran",
        )

        cls.destination = Airport.objects.create(
            name="Security Destination Airport",
            icao_code="OISB",
            iata_code="SDA",
            country="Iran",
            city="Mashhad",
        )

        departure = (
            timezone.now()
            + timedelta(hours=2)
        )

        cls.flight = Flight.objects.create(
            flight_number="SEC100",
            airline=cls.airline,
            aircraft=cls.aircraft,
            origin=cls.origin,
            destination=cls.destination,
            departure_time=departure,
            arrival_time=(
                departure
                + timedelta(hours=1)
            ),
        )

        cls.admin = User.objects.create_user(
            username="security-admin",
            password="test-password",
            role="ADMIN",
        )

        cls.security_officer = (
            User.objects.create_user(
                username="security-officer",
                password="test-password",
                role="SECURITY_OFFICER",
            )
        )

        cls.second_officer = (
            User.objects.create_user(
                username="second-officer",
                password="test-password",
                role="SECURITY_OFFICER",
            )
        )

        cls.ground_staff = (
            User.objects.create_user(
                username="security-ground",
                password="test-password",
                role="GROUND_STAFF",
            )
        )

        cls.report = (
            SecurityReport.objects.create(
                flight=cls.flight,
                officer=cls.security_officer,
                report_type="ACCESS",
                severity="HIGH",
                description=(
                    "Unauthorized access attempt "
                    "reported near the gate."
                ),
                location="Terminal 1 - Gate A03",
                status="OPEN",
            )
        )

    def test_reference_uses_security_prefix(
        self,
    ):
        self.assertEqual(
            self.report.reference,
            f"SEC-{self.report.pk:06d}",
        )

    def test_open_incident_can_only_start_investigation(
        self,
    ):
        choices = (
            available_security_status_choices(
                "OPEN"
            )
        )

        self.assertEqual(
            choices,
            [
                (
                    "INVESTIGATING",
                    "Investigating",
                )
            ],
        )

    def test_security_officer_can_be_assigned(
        self,
    ):
        report = assign_security_officer(
            report_id=self.report.pk,
            officer=self.second_officer,
            actor=self.admin,
        )

        self.assertEqual(
            report.officer,
            self.second_officer,
        )

        self.assertTrue(
            AuditLog.objects.filter(
                action=AuditLog.Action.ASSIGN,
                entity_id=str(
                    self.report.pk
                ),
                actor=self.admin,
            ).exists()
        )

    def test_non_security_user_cannot_be_assigned(
        self,
    ):
        with self.assertRaises(
            InvalidSecurityAssignment
        ):
            assign_security_officer(
                report_id=self.report.pk,
                officer=self.ground_staff,
                actor=self.admin,
            )

    def test_investigation_requires_assigned_officer(
        self,
    ):
        unassigned_report = (
            SecurityReport.objects.create(
                flight=self.flight,
                officer=None,
                report_type="BAGGAGE",
                severity="MEDIUM",
                description=(
                    "Unattended baggage "
                    "requires assessment."
                ),
                location="Terminal 1",
            )
        )

        with self.assertRaises(
            InvalidSecurityTransition
        ):
            transition_security_report_status(
                report_id=(
                    unassigned_report.pk
                ),
                new_status="INVESTIGATING",
                actor=self.admin,
            )

    def test_open_incident_can_start_investigation(
        self,
    ):
        report = (
            transition_security_report_status(
                report_id=self.report.pk,
                new_status="INVESTIGATING",
                actor=self.security_officer,
            )
        )

        self.assertEqual(
            report.status,
            "INVESTIGATING",
        )

        self.assertTrue(
            AuditLog.objects.filter(
                action=(
                    AuditLog.Action.STATUS_CHANGE
                ),
                entity_id=str(
                    self.report.pk
                ),
                actor=self.security_officer,
            ).exists()
        )

    def test_open_incident_cannot_resolve_directly(
        self,
    ):
        with self.assertRaises(
            InvalidSecurityTransition
        ):
            transition_security_report_status(
                report_id=self.report.pk,
                new_status="RESOLVED",
                actor=self.security_officer,
                resolution_notes=(
                    "Issue resolved."
                ),
            )

    def test_resolution_requires_notes(self):
        SecurityReport.objects.filter(
            pk=self.report.pk
        ).update(
            status="INVESTIGATING"
        )

        with self.assertRaises(
            InvalidSecurityTransition
        ):
            transition_security_report_status(
                report_id=self.report.pk,
                new_status="RESOLVED",
                actor=self.security_officer,
                resolution_notes="",
            )

    def test_resolving_incident_sets_resolution_data(
        self,
    ):
        transition_security_report_status(
            report_id=self.report.pk,
            new_status="INVESTIGATING",
            actor=self.security_officer,
        )

        report = (
            transition_security_report_status(
                report_id=self.report.pk,
                new_status="RESOLVED",
                actor=self.security_officer,
                resolution_notes=(
                    "Access credentials were "
                    "verified and the restricted "
                    "area was secured."
                ),
            )
        )

        self.assertEqual(
            report.status,
            "RESOLVED",
        )

        self.assertIsNotNone(
            report.resolved_at
        )

        self.assertEqual(
            report.resolution_notes,
            (
                "Access credentials were "
                "verified and the restricted "
                "area was secured."
            ),
        )

        status_events = (
            AuditLog.objects.filter(
                action=(
                    AuditLog.Action.STATUS_CHANGE
                ),
                entity_id=str(
                    self.report.pk
                ),
            )
        )

        self.assertEqual(
            status_events.count(),
            2,
        )

    def test_resolved_incident_can_be_reopened(
        self,
    ):
        SecurityReport.objects.filter(
            pk=self.report.pk
        ).update(
            status="RESOLVED",
            resolution_notes=(
                "Initial resolution."
            ),
            resolved_at=timezone.now(),
        )

        report = (
            transition_security_report_status(
                report_id=self.report.pk,
                new_status="INVESTIGATING",
                actor=self.security_officer,
            )
        )

        self.assertEqual(
            report.status,
            "INVESTIGATING",
        )

        self.assertIsNone(
            report.resolved_at
        )

    def test_resolved_incident_can_be_closed(
        self,
    ):
        SecurityReport.objects.filter(
            pk=self.report.pk
        ).update(
            status="RESOLVED",
            resolution_notes=(
                "Incident resolved."
            ),
            resolved_at=timezone.now(),
        )

        report = (
            transition_security_report_status(
                report_id=self.report.pk,
                new_status="CLOSED",
                actor=self.admin,
            )
        )

        self.assertEqual(
            report.status,
            "CLOSED",
        )

    def test_closed_incident_is_terminal(
        self,
    ):
        SecurityReport.objects.filter(
            pk=self.report.pk
        ).update(
            status="CLOSED"
        )

        with self.assertRaises(
            InvalidSecurityTransition
        ):
            transition_security_report_status(
                report_id=self.report.pk,
                new_status="INVESTIGATING",
                actor=self.admin,
            )

        self.assertEqual(
            available_security_status_choices(
                "CLOSED"
            ),
            [],
        )