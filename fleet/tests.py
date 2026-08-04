from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from .forms import AircraftForm, AircraftTypeForm
from airlines.models import Airline

from .models import Aircraft, AircraftType


User = get_user_model()


class FleetAuthorizationTests(TestCase):
    def setUp(self):
        self.airline = Airline.objects.create(
            name="Resume Air",
            iata_code="RA",
            icao_code="RSA",
            country="Iran",
        )

        self.aircraft_type = AircraftType.objects.create(
            manufacturer="Airbus",
            model="A320",
            passenger_capacity=180,
            range_km=6100,
        )

        self.aircraft = Aircraft.objects.create(
            airline=self.airline,
            aircraft_type=self.aircraft_type,
            registration_number="EP-RSM",
            status="ACTIVE",
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

    def test_aircraft_list_requires_authentication(self):
        response = self.client.get(
            reverse("aircraft_list")
        )

        expected_url = (
            f"{reverse('login')}"
            f"?next={reverse('aircraft_list')}"
        )

        self.assertRedirects(response, expected_url)

    def test_non_admin_cannot_create_aircraft(self):
        self.client.force_login(self.ground_staff)

        response = self.client.get(
            reverse("aircraft_create")
        )

        self.assertEqual(response.status_code, 403)

    def test_superuser_can_open_aircraft_type_create(self):
        superuser = User.objects.create_superuser(
            username="root-admin",
            password="test-password",
            email="root@example.com",
        )

        self.client.force_login(superuser)

        response = self.client.get(
            reverse("aircraft_type_create")
        )

        self.assertEqual(response.status_code, 200)

    def test_status_change_rejects_get_request(self):
        self.client.force_login(self.admin)

        response = self.client.get(
            reverse(
                "aircraft_change_status",
                args=[self.aircraft.pk],
            )
        )

        self.assertEqual(response.status_code, 405)

    def test_admin_can_change_aircraft_status(self):
        self.client.force_login(self.admin)

        response = self.client.post(
            reverse(
                "aircraft_change_status",
                args=[self.aircraft.pk],
            )
        )

        self.assertRedirects(
            response,
            reverse("aircraft_list"),
        )

        self.aircraft.refresh_from_db()

        self.assertEqual(
            self.aircraft.status,
            "MAINTENANCE",
        )



class FleetFormTests(TestCase):
    def setUp(self):
        self.airline = Airline.objects.create(
            name="Test Air",
            iata_code="TA",
            icao_code="TST",
            country="Iran",
            is_active=True,
        )

        self.aircraft_type = AircraftType.objects.create(
            manufacturer="Airbus",
            model="A321",
            passenger_capacity=220,
            range_km=7400,
            is_active=True,
        )

    def test_invalid_aircraft_specifications_are_rejected(self):
        form = AircraftTypeForm(
            data={
                "manufacturer": "Test",
                "model": "Invalid",
                "passenger_capacity": 1200,
                "range_km": 50,
                "is_active": True,
            }
        )

        self.assertFalse(form.is_valid())

        self.assertIn(
            "passenger_capacity",
            form.errors,
        )

        self.assertIn(
            "range_km",
            form.errors,
        )

    def test_aircraft_identifiers_are_normalized(self):
        form = AircraftForm(
            data={
                "airline": self.airline.id,
                "aircraft_type": self.aircraft_type.id,
                "registration_number": "ep-tst",
                "serial_number": "sn-123",
                "manufacture_year": 2020,
            }
        )

        self.assertTrue(
            form.is_valid(),
            form.errors,
        )

        aircraft = form.save()

        self.assertEqual(
            aircraft.registration_number,
            "EP-TST",
        )

        self.assertEqual(
            aircraft.serial_number,
            "SN-123",
        )

    def test_aircraft_status_is_not_form_editable(self):
        form = AircraftForm()

        self.assertNotIn(
            "status",
            form.fields,
        )