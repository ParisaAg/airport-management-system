from io import StringIO

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from airports.models import Airport
from flights.models import Flight
from operations.models import GroundOperation


User = get_user_model()


class LandingPageTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        output = StringIO()

        call_command(
            "seed_demo",
            password="LandingTest@2026!",
            stdout=output,
        )

    def test_landing_page_is_public(self):
        response = self.client.get(
            reverse("landing")
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertTemplateUsed(
            response,
            "landing.html",
        )

    def test_landing_contains_public_actions(self):
        response = self.client.get(
            reverse("landing")
        )

        self.assertContains(
            response,
            reverse(
                "public_flight_board"
            ),
        )

        self.assertContains(
            response,
            reverse("register"),
        )

        self.assertContains(
            response,
            reverse("login"),
        )

    def test_landing_uses_real_operational_data(
        self,
    ):
        response = self.client.get(
            reverse("landing")
        )

        overview = response.context[
            "overview"
        ]

        today = timezone.localdate()

        expected_flights_today = (
            Flight.objects.filter(
                departure_time__date=today
            ).count()
        )

        expected_active_operations = (
            GroundOperation.objects.filter(
                status="IN_PROGRESS"
            ).count()
        )

        expected_delayed = (
            Flight.objects.filter(
                departure_time__date=today,
                status="DELAYED",
            ).count()
        )

        self.assertEqual(
            overview["flights_today"],
            expected_flights_today,
        )

        self.assertEqual(
            overview[
                "active_operations"
            ],
            expected_active_operations,
        )

        self.assertEqual(
            overview["delayed_flights"],
            expected_delayed,
        )

        self.assertEqual(
            overview["airports"],
            Airport.objects.count(),
        )

        featured_flights = list(
            response.context[
                "featured_flights"
            ]
        )

        self.assertGreater(
            len(featured_flights),
            0,
        )

        self.assertLessEqual(
            len(featured_flights),
            5,
        )

        self.assertContains(
            response,
            "W5104",
        )

    def test_authenticated_user_gets_dashboard_action(
        self,
    ):
        user = User.objects.get(
            username="demo_admin"
        )

        self.client.force_login(user)

        response = self.client.get(
            reverse("landing")
        )

        self.assertContains(
            response,
            reverse("dashboard"),
        )

        self.assertContains(
            response,
            "Dashboard",
        )