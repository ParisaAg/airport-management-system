from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from airlines.models import Airline
from airports.models import Airport
from audit.models import AuditLog
from fleet.models import Aircraft, AircraftType
from flights.models import Flight

from .models import SecurityReport


User = get_user_model()


class SecurityCenterAuthorizationTests(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.airline = Airline.objects.create(
            name="Security Test Airlines",
            iata_code="ST",
            icao_code="SEC",
            country="Iran",
        )

        cls.aircraft_type = AircraftType.objects.create(
            manufacturer="Airbus",
            model="A320 Security Test",
            passenger_capacity=180,
            range_km=6100,
        )

        cls.aircraft = Aircraft.objects.create(
            airline=cls.airline,
            aircraft_type=cls.aircraft_type,
            registration_number="EP-SEC",
        )

        cls.origin = Airport.objects.create(
            name="Security Origin Airport",
            icao_code="OIST",
            iata_code="SOT",
            country="Iran",
            city="Tehran",
        )

        cls.destination = Airport.objects.create(
            name="Security Destination Airport",
            icao_code="OIDT",
            iata_code="SDT",
            country="Iran",
            city="Shiraz",
        )

        departure_time = (
            timezone.now()
            + timedelta(days=1)
        )

        cls.flight = Flight.objects.create(
            flight_number="ST901",
            airline=cls.airline,
            aircraft=cls.aircraft,
            origin=cls.origin,
            destination=cls.destination,
            departure_time=departure_time,
            arrival_time=(
                departure_time
                + timedelta(
                    hours=1,
                    minutes=30,
                )
            ),
        )

        cls.admin = User.objects.create_user(
            username="security-admin",
            password="test-password",
            role="ADMIN",
        )

        cls.manager = User.objects.create_user(
            username="airport-manager",
            password="test-password",
            role="AIRPORT_MANAGER",
        )

        cls.security_officer = (
            User.objects.create_user(
                username="security-officer",
                password="test-password",
                role="SECURITY_OFFICER",
            )
        )

        cls.second_security_officer = (
            User.objects.create_user(
                username="security-officer-two",
                password="test-password",
                role="SECURITY_OFFICER",
            )
        )

        cls.ground_staff = User.objects.create_user(
            username="security-ground",
            password="test-password",
            role="GROUND_STAFF",
        )

        cls.viewer = User.objects.create_user(
            username="security-viewer",
            password="test-password",
            role="VIEWER",
        )

        cls.report = SecurityReport.objects.create(
            flight=cls.flight,
            report_type="ACCESS",
            severity="HIGH",
            location="Terminal 1 / Gate A1",
            description=(
                "Unauthorized access attempt "
                "detected near boarding gate."
            ),
            status="OPEN",
        )

    def test_anonymous_user_is_redirected_from_security_center(
        self,
    ):
        response = self.client.get(
            reverse("security:list")
        )

        expected_url = (
            f"{reverse('login')}"
            f"?next={reverse('security:list')}"
        )

        self.assertRedirects(
            response,
            expected_url,
        )

    def test_admin_can_access_security_center(
        self,
    ):
        self.client.force_login(
            self.admin
        )

        response = self.client.get(
            reverse("security:list")
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertContains(
            response,
            self.report.reference,
        )

    def test_security_officer_can_access_security_center(
        self,
    ):
        self.client.force_login(
            self.security_officer
        )

        response = self.client.get(
            reverse("security:list")
        )

        self.assertEqual(
            response.status_code,
            200,
        )

    def test_airport_manager_has_read_access(
        self,
    ):
        self.client.force_login(
            self.manager
        )

        list_response = self.client.get(
            reverse("security:list")
        )

        detail_response = self.client.get(
            reverse(
                "security:detail",
                args=[
                    self.report.id,
                ],
            )
        )

        self.assertEqual(
            list_response.status_code,
            200,
        )

        self.assertEqual(
            detail_response.status_code,
            200,
        )

    def test_viewer_cannot_access_security_center(
        self,
    ):
        self.client.force_login(
            self.viewer
        )

        response = self.client.get(
            reverse("security:list")
        )

        self.assertEqual(
            response.status_code,
            403,
        )

    def test_ground_staff_cannot_access_security_center(
        self,
    ):
        self.client.force_login(
            self.ground_staff
        )

        response = self.client.get(
            reverse("security:list")
        )

        self.assertEqual(
            response.status_code,
            403,
        )

    def test_airport_manager_cannot_create_incident(
        self,
    ):
        self.client.force_login(
            self.manager
        )

        response = self.client.get(
            reverse("security:create")
        )

        self.assertEqual(
            response.status_code,
            403,
        )

    def test_security_officer_can_open_create_page(
        self,
    ):
        self.client.force_login(
            self.security_officer
        )

        response = self.client.get(
            reverse("security:create")
        )

        self.assertEqual(
            response.status_code,
            200,
        )

    def test_admin_can_create_security_incident(
        self,
    ):
        self.client.force_login(
            self.admin
        )

        response = self.client.post(
            reverse("security:create"),
            {
                "flight": self.flight.id,
                "report_type": "BAGGAGE",
                "severity": "MEDIUM",
                "location": "Baggage Hall 2",
                "officer": (
                    self.security_officer.id
                ),
                "description": (
                    "Unattended baggage discovered "
                    "during security inspection."
                ),
            },
        )

        report = SecurityReport.objects.get(
            report_type="BAGGAGE",
        )

        self.assertRedirects(
            response,
            reverse(
                "security:detail",
                args=[
                    report.id,
                ],
            ),
        )

        self.assertEqual(
            report.status,
            "OPEN",
        )

        self.assertEqual(
            report.officer,
            self.security_officer,
        )

        self.assertTrue(
            AuditLog.objects.filter(
                actor=self.admin,
                action=(
                    AuditLog.Action.CREATE
                ),
                entity_id=str(
                    report.id
                ),
            ).exists()
        )

    def test_create_incident_requires_valid_data(
        self,
    ):
        self.client.force_login(
            self.admin
        )

        response = self.client.post(
            reverse("security:create"),
            {
                "flight": "",
                "report_type": "",
                "severity": "",
                "location": "",
                "officer": "",
                "description": "",
            },
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertEqual(
            SecurityReport.objects.count(),
            1,
        )

    def test_airport_manager_cannot_assign_officer(
        self,
    ):
        self.client.force_login(
            self.manager
        )

        response = self.client.post(
            reverse(
                "security:assign",
                args=[
                    self.report.id,
                ],
            ),
            {
                "officer": (
                    self.security_officer.id
                ),
            },
        )

        self.assertEqual(
            response.status_code,
            403,
        )

        self.report.refresh_from_db()

        self.assertIsNone(
            self.report.officer,
        )

    def test_security_officer_can_assign_incident(
        self,
    ):
        self.client.force_login(
            self.security_officer
        )

        response = self.client.post(
            reverse(
                "security:assign",
                args=[
                    self.report.id,
                ],
            ),
            {
                "officer": (
                    self.second_security_officer.id
                ),
            },
        )

        self.assertRedirects(
            response,
            reverse(
                "security:detail",
                args=[
                    self.report.id,
                ],
            ),
        )

        self.report.refresh_from_db()

        self.assertEqual(
            self.report.officer,
            self.second_security_officer,
        )

        self.assertTrue(
            AuditLog.objects.filter(
                actor=self.security_officer,
                action=(
                    AuditLog.Action.ASSIGN
                ),
                entity_id=str(
                    self.report.id
                ),
            ).exists()
        )

    def test_assignment_endpoint_rejects_get_request(
        self,
    ):
        self.client.force_login(
            self.admin
        )

        response = self.client.get(
            reverse(
                "security:assign",
                args=[
                    self.report.id,
                ],
            )
        )

        self.assertEqual(
            response.status_code,
            405,
        )

    def test_status_endpoint_rejects_get_request(
        self,
    ):
        self.client.force_login(
            self.admin
        )

        response = self.client.get(
            reverse(
                "security:change_status",
                args=[
                    self.report.id,
                ],
            )
        )

        self.assertEqual(
            response.status_code,
            405,
        )

    def test_security_officer_can_start_investigation(
        self,
    ):
        self.report.officer = (
            self.security_officer
        )

        self.report.save(
            update_fields=[
                "officer",
            ]
        )

        self.client.force_login(
            self.security_officer
        )

        response = self.client.post(
            reverse(
                "security:change_status",
                args=[
                    self.report.id,
                ],
            ),
            {
                "status": (
                    "INVESTIGATING"
                ),
            },
        )

        self.assertRedirects(
            response,
            reverse(
                "security:detail",
                args=[
                    self.report.id,
                ],
            ),
        )

        self.report.refresh_from_db()

        self.assertEqual(
            self.report.status,
            "INVESTIGATING",
        )

        self.assertTrue(
            AuditLog.objects.filter(
                actor=self.security_officer,
                action=(
                    AuditLog.Action.STATUS_CHANGE
                ),
                entity_id=str(
                    self.report.id
                ),
            ).exists()
        )

    def test_airport_manager_cannot_change_status(
        self,
    ):
        self.report.officer = (
            self.security_officer
        )

        self.report.save(
            update_fields=[
                "officer",
            ]
        )

        self.client.force_login(
            self.manager
        )

        response = self.client.post(
            reverse(
                "security:change_status",
                args=[
                    self.report.id,
                ],
            ),
            {
                "status": (
                    "INVESTIGATING"
                ),
            },
        )

        self.assertEqual(
            response.status_code,
            403,
        )

        self.report.refresh_from_db()

        self.assertEqual(
            self.report.status,
            "OPEN",
        )

    def test_viewer_cannot_change_incident_status(
        self,
    ):
        self.report.officer = (
            self.security_officer
        )

        self.report.save(
            update_fields=[
                "officer",
            ]
        )

        self.client.force_login(
            self.viewer
        )

        response = self.client.post(
            reverse(
                "security:change_status",
                args=[
                    self.report.id,
                ],
            ),
            {
                "status": (
                    "INVESTIGATING"
                ),
            },
        )

        self.assertEqual(
            response.status_code,
            403,
        )

        self.report.refresh_from_db()

        self.assertEqual(
            self.report.status,
            "OPEN",
        )

    def test_security_search_filters_incidents(
        self,
    ):
        SecurityReport.objects.create(
            flight=self.flight,
            report_type="BAGGAGE",
            severity="LOW",
            location="Remote Baggage Area",
            description=(
                "Routine baggage security report."
            ),
        )

        self.client.force_login(
            self.admin
        )

        response = self.client.get(
            reverse("security:list"),
            {
                "search": (
                    "Unauthorized access"
                ),
            },
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertContains(
            response,
            self.report.reference,
        )

        self.assertNotContains(
            response,
            "Remote Baggage Area",
        )

    def test_unassigned_filter_only_returns_unassigned_incidents(
        self,
    ):
        assigned_report = (
            SecurityReport.objects.create(
                flight=self.flight,
                officer=(
                    self.security_officer
                ),
                report_type="AIRCRAFT",
                severity="MEDIUM",
                location="Apron Zone",
                description=(
                    "Assigned aircraft "
                    "security inspection."
                ),
            )
        )

        self.client.force_login(
            self.admin
        )

        response = self.client.get(
            reverse("security:list"),
            {
                "assignment": (
                    "UNASSIGNED"
                ),
            },
        )

        self.assertContains(
            response,
            self.report.reference,
        )

        self.assertNotContains(
            response,
            assigned_report.reference,
        )

    def test_assigned_to_me_filter_only_returns_users_incidents(
        self,
    ):
        own_report = SecurityReport.objects.create(
            flight=self.flight,
            officer=self.security_officer,
            report_type="PASSENGER",
            severity="MEDIUM",
            location="Departure Hall",
            description=(
                "Passenger security incident."
            ),
        )

        SecurityReport.objects.create(
            flight=self.flight,
            officer=(
                self.second_security_officer
            ),
            report_type="OTHER",
            severity="LOW",
            location="Terminal Office",
            description=(
                "Another officer incident."
            ),
        )

        self.client.force_login(
            self.security_officer
        )

        response = self.client.get(
            reverse("security:list"),
            {
                "assignment": "MINE",
            },
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertContains(
            response,
            own_report.reference,
        )

        self.assertNotContains(
            response,
            "Terminal Office",
        )