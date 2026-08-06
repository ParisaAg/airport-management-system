from datetime import timedelta
from io import StringIO

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse

from airlines.models import Airline
from airports.models import Airport, Gate, Terminal
from audit.models import AuditLog
from fleet.models import Aircraft, AircraftType
from flights.models import Flight, GateAssignment
from notifications.models import Notification
from operations.models import GroundOperation, OperationType
from passenger_service.models import PassengerRequest
from security.models import SecurityReport

from .permissions import ADMIN, has_role


User = get_user_model()


class AuthenticationSecurityTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="ground-user",
            password="test-password",
            role="GROUND_STAFF",
        )

    def test_profile_requires_authentication(self):
        response = self.client.get(
            reverse("profile")
        )

        expected_url = (
            f"{reverse('login')}"
            f"?next={reverse('profile')}"
        )

        self.assertRedirects(
            response,
            expected_url,
        )

    def test_authenticated_user_is_redirected_from_login(
        self,
    ):
        self.client.force_login(
            self.user
        )

        response = self.client.get(
            reverse("login")
        )

        self.assertRedirects(
            response,
            reverse("dashboard"),
        )

    def test_logout_rejects_get_request(self):
        self.client.force_login(
            self.user
        )

        response = self.client.get(
            reverse("logout")
        )

        self.assertEqual(
            response.status_code,
            405,
        )

    def test_logout_accepts_post_and_ends_session(
        self,
    ):
        self.client.force_login(
            self.user
        )

        response = self.client.post(
            reverse("logout")
        )

        self.assertRedirects(
            response,
            reverse("landing"),
        )

        self.assertNotIn(
            "_auth_user_id",
            self.client.session,
        )

    def test_superuser_is_accepted_for_admin_role(
        self,
    ):
        superuser = (
            User.objects.create_superuser(
                username="root-admin",
                password="test-password",
                email="admin@example.com",
            )
        )

        self.assertTrue(
            has_role(
                superuser,
                [ADMIN],
            )
        )


class DemoSeedCommandTests(TestCase):
    demo_password = "DemoTest@2026!"

    def run_seed(self):
        output = StringIO()

        call_command(
            "seed_demo",
            password=self.demo_password,
            stdout=output,
        )

        return output.getvalue()

    def test_seed_creates_complete_demo_dataset(
        self,
    ):
        output = self.run_seed()

        self.assertIn(
            "Demo dataset is ready.",
            output,
        )

        self.assertEqual(
            Airport.objects.count(),
            4,
        )
        self.assertEqual(
            Terminal.objects.count(),
            6,
        )
        self.assertEqual(
            Gate.objects.count(),
            12,
        )
        self.assertEqual(
            Airline.objects.count(),
            3,
        )
        self.assertEqual(
            AircraftType.objects.count(),
            4,
        )
        self.assertEqual(
            Aircraft.objects.count(),
            6,
        )
        self.assertEqual(
            Flight.objects.count(),
            12,
        )
        self.assertEqual(
            GateAssignment.objects.count(),
            7,
        )
        self.assertEqual(
            OperationType.objects.count(),
            6,
        )
        self.assertEqual(
            GroundOperation.objects.count(),
            11,
        )
        self.assertEqual(
            SecurityReport.objects.count(),
            4,
        )
        self.assertEqual(
            PassengerRequest.objects.count(),
            5,
        )
        self.assertEqual(
            Notification.objects.count(),
            6,
        )
        self.assertEqual(
            AuditLog.objects.count(),
            4,
        )

    def test_seed_creates_all_demo_roles(
        self,
    ):
        self.run_seed()

        expected_roles = {
            "demo_admin": "ADMIN",
            "demo_manager": (
                "AIRPORT_MANAGER"
            ),
            "demo_ground": "GROUND_STAFF",
            "demo_security": (
                "SECURITY_OFFICER"
            ),
            "demo_passenger": (
                "PASSENGER_SERVICE"
            ),
            "demo_iran_operator": (
                "AIRLINE_OPERATOR"
            ),
            "demo_mahan_operator": (
                "AIRLINE_OPERATOR"
            ),
        }

        for username, role in (
            expected_roles.items()
        ):
            user = User.objects.get(
                username=username
            )

            self.assertEqual(
                user.role,
                role,
            )

            self.assertTrue(
                user.check_password(
                    self.demo_password
                )
            )

    def test_airline_operator_is_linked_to_airline(
        self,
    ):
        self.run_seed()

        iran_operator = User.objects.get(
            username="demo_iran_operator"
        )

        mahan_operator = User.objects.get(
            username="demo_mahan_operator"
        )

        self.assertEqual(
            iran_operator.airline.iata_code,
            "IR",
        )

        self.assertEqual(
            mahan_operator.airline.iata_code,
            "W5",
        )

    def test_demo_aircraft_belongs_to_flight_airline(
        self,
    ):
        self.run_seed()

        for flight in (
            Flight.objects
            .select_related(
                "airline",
                "aircraft",
            )
            .all()
        ):
            self.assertEqual(
                flight.aircraft.airline_id,
                flight.airline_id,
                msg=(
                    f"{flight.flight_number} "
                    "uses an aircraft belonging "
                    "to another airline."
                ),
            )

    def test_delayed_flight_has_operational_context(
        self,
    ):
        self.run_seed()

        flight = (
            Flight.objects
            .select_related(
                "airline",
                "origin",
                "destination",
            )
            .get(
                flight_number="W5104"
            )
        )

        self.assertEqual(
            flight.status,
            "DELAYED",
        )

        self.assertEqual(
            flight.airline.iata_code,
            "W5",
        )

        self.assertEqual(
            flight.origin.iata_code,
            "IKA",
        )

        self.assertEqual(
            flight.destination.iata_code,
            "MHD",
        )

        self.assertEqual(
            (
                flight.estimated_departure_time
                - flight.departure_time
            ),
            timedelta(minutes=45),
        )

        self.assertTrue(
            flight.disruption_reason
        )

        gate_assignment = (
            flight.gate_assignments.get(
                status="ACTIVE"
            )
        )

        self.assertEqual(
            gate_assignment.gate.code,
            "IKA-A03",
        )

        operation_names = set(
            flight.ground_operations
            .values_list(
                "operation_type__name",
                flat=True,
            )
        )

        self.assertSetEqual(
            operation_names,
            {
                "Baggage Handling",
                "Refueling",
                "Technical Inspection",
            },
        )

        self.assertTrue(
            flight.security_reports.exists()
        )

        self.assertTrue(
            flight.passenger_requests.exists()
        )

    def test_demo_gate_assignments_do_not_conflict(
        self,
    ):
        self.run_seed()

        active_assignments = (
            GateAssignment.objects
            .filter(status="ACTIVE")
        )

        gate_ids = list(
            active_assignments.values_list(
                "gate_id",
                flat=True,
            )
        )

        self.assertEqual(
            len(gate_ids),
            len(set(gate_ids)),
        )

    def test_seed_is_idempotent(self):
        self.run_seed()

        counts_before = {
            "users": User.objects.count(),
            "airports": (
                Airport.objects.count()
            ),
            "terminals": (
                Terminal.objects.count()
            ),
            "gates": Gate.objects.count(),
            "airlines": (
                Airline.objects.count()
            ),
            "aircraft_types": (
                AircraftType.objects.count()
            ),
            "aircraft": (
                Aircraft.objects.count()
            ),
            "flights": (
                Flight.objects.count()
            ),
            "gate_assignments": (
                GateAssignment.objects.count()
            ),
            "operation_types": (
                OperationType.objects.count()
            ),
            "operations": (
                GroundOperation.objects.count()
            ),
            "security": (
                SecurityReport.objects.count()
            ),
            "passenger": (
                PassengerRequest.objects.count()
            ),
            "notifications": (
                Notification.objects.count()
            ),
            "audit": (
                AuditLog.objects.count()
            ),
        }

        self.run_seed()

        counts_after = {
            "users": User.objects.count(),
            "airports": (
                Airport.objects.count()
            ),
            "terminals": (
                Terminal.objects.count()
            ),
            "gates": Gate.objects.count(),
            "airlines": (
                Airline.objects.count()
            ),
            "aircraft_types": (
                AircraftType.objects.count()
            ),
            "aircraft": (
                Aircraft.objects.count()
            ),
            "flights": (
                Flight.objects.count()
            ),
            "gate_assignments": (
                GateAssignment.objects.count()
            ),
            "operation_types": (
                OperationType.objects.count()
            ),
            "operations": (
                GroundOperation.objects.count()
            ),
            "security": (
                SecurityReport.objects.count()
            ),
            "passenger": (
                PassengerRequest.objects.count()
            ),
            "notifications": (
                Notification.objects.count()
            ),
            "audit": (
                AuditLog.objects.count()
            ),
        }

        self.assertDictEqual(
            counts_before,
            counts_after,
        )

    def test_seed_preserves_existing_data(
        self,
    ):
        existing_airport = (
            Airport.objects.create(
                name="Existing Test Airport",
                iata_code="TST",
                icao_code="TEST",
                country="Test Country",
                city="Test City",
            )
        )

        self.run_seed()

        self.assertTrue(
            Airport.objects.filter(
                pk=existing_airport.pk
            ).exists()
        )




class RegistrationFlowTests(TestCase):
    def test_registration_page_is_available(self):
        response = self.client.get(
            reverse("register")
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertTemplateUsed(
            response,
            "accounts/register.html",
        )

    def test_registration_creates_viewer_and_logs_user_in(
        self,
    ):
        response = self.client.post(
            reverse("register"),
            {
                "first_name": "Parisa",
                "last_name": "Demo",
                "username": "parisa-viewer",
                "email": "parisa@example.com",
                "password1": "AirportTest@2026!",
                "password2": "AirportTest@2026!",
            },
        )

        user = User.objects.get(
            username="parisa-viewer"
        )

        self.assertEqual(
            user.role,
            "VIEWER",
        )

        self.assertEqual(
            user.email,
            "parisa@example.com",
        )

        self.assertTrue(
            user.check_password(
                "AirportTest@2026!"
            )
        )

        self.assertRedirects(
            response,
            reverse("dashboard"),
        )

        self.assertEqual(
            int(
                self.client.session[
                    "_auth_user_id"
                ]
            ),
            user.pk,
        )

    def test_duplicate_email_is_rejected(self):
        User.objects.create_user(
            username="existing-viewer",
            email="viewer@example.com",
            password="AirportTest@2026!",
            role="VIEWER",
        )

        response = self.client.post(
            reverse("register"),
            {
                "first_name": "Another",
                "last_name": "Viewer",
                "username": "another-viewer",
                "email": "VIEWER@example.com",
                "password1": "AirportTest@2026!",
                "password2": "AirportTest@2026!",
            },
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertFalse(
            User.objects.filter(
                username="another-viewer"
            ).exists()
        )

        self.assertContains(
            response,
            (
                "An account with this email "
                "already exists."
            ),
        )

    def test_authenticated_user_cannot_open_register(
        self,
    ):
        user = User.objects.create_user(
            username="authenticated-viewer",
            password="AirportTest@2026!",
            role="VIEWER",
        )

        self.client.force_login(user)

        response = self.client.get(
            reverse("register")
        )

        self.assertRedirects(
            response,
            reverse("dashboard"),
        )

    def test_new_user_default_role_is_viewer(self):
        user = User.objects.create_user(
            username="default-role-user",
            password="AirportTest@2026!",
        )

        self.assertEqual(
            user.role,
            "VIEWER",
        )

    def test_viewer_does_not_have_admin_role(self):
        user = User.objects.create_user(
            username="limited-viewer",
            password="AirportTest@2026!",
            role="VIEWER",
        )

        self.assertFalse(
            has_role(
                user,
                [ADMIN],
            )
        )