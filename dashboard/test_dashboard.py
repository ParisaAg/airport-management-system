from io import StringIO

from django.contrib.auth import (
    get_user_model,
)
from django.test import TestCase
from django.urls import reverse

from flights.models import Flight
from operations.models import GroundOperation
from passenger_service.models import (
    PassengerRequest,
)
from security.models import SecurityReport


User = get_user_model()


class OperationsDashboardTests(TestCase):

    @classmethod
    def setUpTestData(cls):
        output = StringIO()

        call_command_options = {
            "password": (
                "DashboardTest@2026!"
            ),
            "stdout": output,
        }

        from django.core.management import (
            call_command,
        )

        call_command(
            "seed_demo",
            **call_command_options,
        )

        cls.admin = User.objects.get(
            username="demo_admin"
        )

        cls.manager = User.objects.get(
            username="demo_manager"
        )

        cls.ground_staff = User.objects.get(
            username="demo_ground"
        )

        cls.security_officer = (
            User.objects.get(
                username="demo_security"
            )
        )

        cls.passenger_agent = (
            User.objects.get(
                username="demo_passenger"
            )
        )

        cls.airline_operator = (
            User.objects.get(
                username="demo_iran_operator"
            )
        )

    def test_dashboard_requires_authentication(
        self,
    ):
        response = self.client.get(
            reverse("dashboard")
        )

        expected_url = (
            f"{reverse('login')}"
            f"?next={reverse('dashboard')}"
        )

        self.assertRedirects(
            response,
            expected_url,
        )

    def test_admin_dashboard_loads_operational_center(
        self,
    ):
        self.client.force_login(
            self.admin
        )

        response = self.client.get(
            reverse("dashboard")
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertTemplateUsed(
            response,
            "dashboard/index.html",
        )

        self.assertContains(
            response,
            "Operations Dashboard",
        )

        self.assertContains(
            response,
            reverse(
                "public_flight_board"
            ),
        )

        self.assertContains(
            response,
            reverse("security:list"),
        )

        self.assertContains(
            response,
            reverse(
                "passenger_service:list"
            ),
        )

    def test_admin_flight_statistics_use_all_flights(
        self,
    ):
        self.client.force_login(
            self.admin
        )

        response = self.client.get(
            reverse("dashboard")
        )

        statistics = response.context[
            "flight_stats"
        ]

        self.assertEqual(
            statistics["total"],
            Flight.objects.count(),
        )

        self.assertEqual(
            statistics["delayed"],
            Flight.objects.filter(
                status="DELAYED"
            ).count(),
        )

        self.assertEqual(
            statistics["arrived"],
            Flight.objects.filter(
                status="ARRIVED"
            ).count(),
        )

    def test_security_statistics_only_count_active_critical_reports(
        self,
    ):
        SecurityReport.objects.create(
            flight=Flight.objects.first(),
            officer=self.security_officer,
            report_type="ACCESS",
            severity="CRITICAL",
            location="Closed test incident",
            description=(
                "This critical incident "
                "is already closed."
            ),
            status="CLOSED",
        )

        self.client.force_login(
            self.admin
        )

        response = self.client.get(
            reverse("dashboard")
        )

        expected_critical = (
            SecurityReport.objects.filter(
                severity="CRITICAL",
                status__in=(
                    "OPEN",
                    "INVESTIGATING",
                ),
            ).count()
        )

        self.assertEqual(
            response.context[
                "security_stats"
            ]["critical"],
            expected_critical,
        )

    def test_passenger_statistics_only_count_active_urgent_requests(
        self,
    ):
        PassengerRequest.objects.create(
            flight=Flight.objects.first(),
            passenger_name=(
                "Completed Urgent Passenger"
            ),
            request_type=(
                "SPECIAL_ASSISTANCE"
            ),
            priority="URGENT",
            service_location=(
                "Completed service desk"
            ),
            description=(
                "Already completed urgent "
                "service request."
            ),
            status="COMPLETED",
        )

        self.client.force_login(
            self.admin
        )

        response = self.client.get(
            reverse("dashboard")
        )

        expected_urgent = (
            PassengerRequest.objects.filter(
                priority="URGENT",
                status__in=(
                    "OPEN",
                    "ASSIGNED",
                    "IN_PROGRESS",
                ),
            ).count()
        )

        self.assertEqual(
            response.context[
                "passenger_stats"
            ]["urgent"],
            expected_urgent,
        )

    def test_airline_operator_only_receives_own_airline_flights(
        self,
    ):
        self.client.force_login(
            self.airline_operator
        )

        response = self.client.get(
            reverse("dashboard")
        )

        expected_flights = (
            Flight.objects.filter(
                airline_id=(
                    self.airline_operator
                    .airline_id
                )
            )
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertEqual(
            response.context[
                "flight_stats"
            ]["total"],
            expected_flights.count(),
        )

        self.assertEqual(
            response.context[
                "airline_stats"
            ]["total"],
            expected_flights.count(),
        )

        for flight in response.context[
            "recent_flights"
        ]:
            self.assertEqual(
                flight.airline_id,
                self.airline_operator
                .airline_id,
            )

    def test_ground_staff_only_receives_assigned_operations(
        self,
    ):
        self.client.force_login(
            self.ground_staff
        )

        response = self.client.get(
            reverse("dashboard")
        )

        expected_operations = (
            GroundOperation.objects.filter(
                assigned_staff=(
                    self.ground_staff
                )
            )
        )

        self.assertEqual(
            response.context[
                "operation_stats"
            ]["total"],
            expected_operations.count(),
        )

        for operation in response.context[
            "recent_operations"
        ]:
            self.assertEqual(
                operation.assigned_staff_id,
                self.ground_staff.id,
            )

        for operation in response.context[
            "active_operations"
        ]:
            self.assertEqual(
                operation.assigned_staff_id,
                self.ground_staff.id,
            )

    def test_security_officer_receives_security_context(
        self,
    ):
        self.client.force_login(
            self.security_officer
        )

        response = self.client.get(
            reverse("dashboard")
        )

        self.assertTrue(
            response.context[
                "can_view_security"
            ]
        )

        self.assertFalse(
            response.context[
                "can_view_passenger"
            ]
        )

        self.assertEqual(
            response.context[
                "security_stats"
            ]["total"],
            SecurityReport.objects.count(),
        )

        self.assertContains(
            response,
            reverse("security:list"),
        )

    def test_passenger_agent_receives_passenger_context(
        self,
    ):
        self.client.force_login(
            self.passenger_agent
        )

        response = self.client.get(
            reverse("dashboard")
        )

        self.assertTrue(
            response.context[
                "can_view_passenger"
            ]
        )

        self.assertFalse(
            response.context[
                "can_view_security"
            ]
        )

        self.assertEqual(
            response.context[
                "passenger_stats"
            ]["total"],
            PassengerRequest.objects.count(),
        )

        self.assertContains(
            response,
            reverse(
                "passenger_service:list"
            ),
        )

    def test_airport_manager_has_global_read_context(
        self,
    ):
        self.client.force_login(
            self.manager
        )

        response = self.client.get(
            reverse("dashboard")
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertTrue(
            response.context[
                "can_view_global_flights"
            ]
        )

        self.assertTrue(
            response.context[
                "can_view_operations"
            ]
        )

        self.assertTrue(
            response.context[
                "can_view_security"
            ]
        )

        self.assertTrue(
            response.context[
                "can_view_passenger"
            ]
        )