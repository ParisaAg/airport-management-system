from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from .forms import AirlineForm
from .models import Airline


User = get_user_model()


class AirlineAuthorizationTests(TestCase):
    def setUp(self):
        self.airline = Airline.objects.create(
            name="Resume Air",
            iata_code="RA",
            icao_code="RSA",
            country="Iran",
            is_active=True,
        )

        self.admin = User.objects.create_user(
            username="airport-admin",
            password="test-password",
            role="ADMIN",
        )

        self.ground_staff = User.objects.create_user(
            username="ground-user",
            password="test-password",
            role="GROUND_STAFF",
        )

    def test_airline_list_requires_authentication(self):
        response = self.client.get(
            reverse("airline_list")
        )

        expected_url = (
            f"{reverse('login')}"
            f"?next={reverse('airline_list')}"
        )

        self.assertRedirects(response, expected_url)

    def test_non_admin_cannot_create_airline(self):
        self.client.force_login(self.ground_staff)

        response = self.client.get(
            reverse("airline_create")
        )

        self.assertEqual(response.status_code, 403)

    def test_superuser_can_open_airline_create(self):
        superuser = User.objects.create_superuser(
            username="root-admin",
            password="test-password",
            email="root@example.com",
        )

        self.client.force_login(superuser)

        response = self.client.get(
            reverse("airline_create")
        )

        self.assertEqual(response.status_code, 200)

    def test_toggle_status_rejects_get_request(self):
        self.client.force_login(self.admin)

        response = self.client.get(
            reverse(
                "airline_toggle_status",
                args=[self.airline.pk],
            )
        )

        self.assertEqual(response.status_code, 405)

    def test_admin_can_toggle_airline_status(self):
        self.client.force_login(self.admin)

        response = self.client.post(
            reverse(
                "airline_toggle_status",
                args=[self.airline.pk],
            )
        )

        self.assertRedirects(
            response,
            reverse("airline_list"),
        )

        self.airline.refresh_from_db()
        self.assertFalse(self.airline.is_active)

class AirlineFormTests(TestCase):
    def test_codes_are_normalized_to_uppercase(self):
        form = AirlineForm(
            data={
                "name": "Test Airways",
                "iata_code": "ta",
                "icao_code": "taw",
                "country": "Iran",
                "website": "",
                "contact_email": "",
                "is_active": True,
            }
        )

        self.assertTrue(
            form.is_valid(),
            form.errors,
        )

        airline = form.save()

        self.assertEqual(
            airline.iata_code,
            "TA",
        )

        self.assertEqual(
            airline.icao_code,
            "TAW",
        )

    def test_invalid_airline_codes_are_rejected(self):
        form = AirlineForm(
            data={
                "name": "Invalid Airways",
                "iata_code": "TOO",
                "icao_code": "LONG",
                "country": "Iran",
                "website": "",
                "contact_email": "",
                "is_active": True,
            }
        )

        self.assertFalse(form.is_valid())

        self.assertIn(
            "iata_code",
            form.errors,
        )

        self.assertIn(
            "icao_code",
            form.errors,
        )