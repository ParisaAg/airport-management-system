from datetime import timedelta
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone
from django.urls import reverse
from .models import Flight
from airlines.models import Airline
from airports.models import Airport, Gate, Terminal
from fleet.models import Aircraft, AircraftType

from .forms import FlightForm, GateAssignmentForm


User = get_user_model()


class FlightFormTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.airline = Airline.objects.create(
            name="Resume Air",
            iata_code="RA",
            icao_code="RSA",
            country="Iran",
        )

        cls.other_airline = Airline.objects.create(
            name="Other Air",
            iata_code="OA",
            icao_code="OTA",
            country="Iran",
        )

        cls.aircraft_type = AircraftType.objects.create(
            manufacturer="Airbus",
            model="A320",
            passenger_capacity=180,
            range_km=6100,
        )

        cls.aircraft = Aircraft.objects.create(
            airline=cls.airline,
            aircraft_type=cls.aircraft_type,
            registration_number="EP-RSM",
            status="ACTIVE",
        )

        cls.other_aircraft = Aircraft.objects.create(
            airline=cls.other_airline,
            aircraft_type=cls.aircraft_type,
            registration_number="EP-OTH",
            status="ACTIVE",
        )

        cls.origin = Airport.objects.create(
            name="Imam Khomeini International Airport",
            icao_code="OIIE",
            iata_code="IKA",
            country="Iran",
            city="Tehran",
        )

        cls.destination = Airport.objects.create(
            name="Mashhad International Airport",
            icao_code="OIMM",
            iata_code="MHD",
            country="Iran",
            city="Mashhad",
        )

        cls.operator = User.objects.create_user(
            username="airline-operator",
            password="test-password",
            role="AIRLINE_OPERATOR",
            airline=cls.airline,
        )

    def valid_form_data(self):
        departure_time = (
            timezone.now() + timedelta(days=1)
        )

        arrival_time = (
            departure_time + timedelta(hours=1)
        )

        return {
            "flight_number": "ra100",
            "airline": self.airline.id,
            "aircraft": self.aircraft.id,
            "origin": self.origin.id,
            "destination": self.destination.id,
            "departure_time": departure_time.strftime(
                "%Y-%m-%dT%H:%M"
            ),
            "arrival_time": arrival_time.strftime(
                "%Y-%m-%dT%H:%M"
            ),
        }

    def test_status_is_not_form_editable(self):
        form = FlightForm()

        self.assertNotIn(
            "status",
            form.fields,
        )

    def test_flight_number_is_normalized(self):
        form = FlightForm(
            data=self.valid_form_data()
        )

        self.assertTrue(
            form.is_valid(),
            form.errors,
        )

        flight = form.save()

        self.assertEqual(
            flight.flight_number,
            "RA100",
        )

    def test_aircraft_must_belong_to_airline(self):
        data = self.valid_form_data()

        data["aircraft"] = self.other_aircraft.id

        form = FlightForm(data=data)

        self.assertFalse(form.is_valid())

        self.assertIn(
            "aircraft",
            form.errors,
        )

    def test_origin_and_destination_must_differ(self):
        data = self.valid_form_data()

        data["destination"] = self.origin.id

        form = FlightForm(data=data)

        self.assertFalse(form.is_valid())

        self.assertIn(
            "__all__",
            form.errors,
        )

    def test_arrival_must_be_after_departure(self):
        data = self.valid_form_data()

        data["arrival_time"] = data[
            "departure_time"
        ]

        form = FlightForm(data=data)

        self.assertFalse(form.is_valid())

        self.assertIn(
            "__all__",
            form.errors,
        )

    def test_operator_only_sees_own_aircraft(self):
        form = FlightForm(
            user=self.operator
        )

        aircraft_queryset = (
            form.fields["aircraft"].queryset
        )

        self.assertIn(
            self.aircraft,
            aircraft_queryset,
        )

        self.assertNotIn(
            self.other_aircraft,
            aircraft_queryset,
        )

        self.assertTrue(
            form["airline"].is_hidden,
        )

class GateAssignmentFormTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.airport = Airport.objects.create(
            name="Imam Khomeini International Airport",
            icao_code="OIIE",
            iata_code="IKA",
            country="Iran",
            city="Tehran",
        )

        cls.terminal = Terminal.objects.create(
            airport=cls.airport,
            name="Terminal 1",
            code="T1",
        )

        cls.active_gate = Gate.objects.create(
            terminal=cls.terminal,
            name="Gate A1",
            code="A1",
            is_active=True,
        )

        cls.inactive_gate = Gate.objects.create(
            terminal=cls.terminal,
            name="Gate A2",
            code="A2",
            is_active=False,
        )

    def test_only_active_gates_are_available(self):
        form = GateAssignmentForm()

        gate_queryset = form.fields[
            "gate"
        ].queryset

        self.assertIn(
            self.active_gate,
            gate_queryset,
        )

        self.assertNotIn(
            self.inactive_gate,
            gate_queryset,
        )

class FlightAuthorizationTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.airline = Airline.objects.create(
            name="Resume Air",
            iata_code="RA",
            icao_code="RSA",
            country="Iran",
        )

        cls.other_airline = Airline.objects.create(
            name="Other Air",
            iata_code="OA",
            icao_code="OTA",
            country="Iran",
        )

        aircraft_type = AircraftType.objects.create(
            manufacturer="Airbus",
            model="A320",
            passenger_capacity=180,
            range_km=6100,
        )

        cls.aircraft = Aircraft.objects.create(
            airline=cls.airline,
            aircraft_type=aircraft_type,
            registration_number="EP-RSM",
        )

        cls.other_aircraft = Aircraft.objects.create(
            airline=cls.other_airline,
            aircraft_type=aircraft_type,
            registration_number="EP-OTH",
        )

        origin = Airport.objects.create(
            name="Imam Khomeini International Airport",
            icao_code="OIIE",
            iata_code="IKA",
            country="Iran",
            city="Tehran",
        )

        destination = Airport.objects.create(
            name="Mashhad International Airport",
            icao_code="OIMM",
            iata_code="MHD",
            country="Iran",
            city="Mashhad",
        )

        departure_time = (
            timezone.now() + timedelta(days=1)
        )

        cls.flight = Flight.objects.create(
            flight_number="RA100",
            airline=cls.airline,
            aircraft=cls.aircraft,
            origin=origin,
            destination=destination,
            departure_time=departure_time,
            arrival_time=(
                departure_time + timedelta(hours=1)
            ),
        )

        cls.other_flight = Flight.objects.create(
            flight_number="OA200",
            airline=cls.other_airline,
            aircraft=cls.other_aircraft,
            origin=origin,
            destination=destination,
            departure_time=departure_time,
            arrival_time=(
                departure_time + timedelta(hours=1)
            ),
        )

        cls.operator = User.objects.create_user(
            username="airline-operator",
            password="test-password",
            role="AIRLINE_OPERATOR",
            airline=cls.airline,
        )

        cls.operator_without_airline = (
            User.objects.create_user(
                username="unassigned-operator",
                password="test-password",
                role="AIRLINE_OPERATOR",
            )
        )

        cls.ground_staff = User.objects.create_user(
            username="ground-staff",
            password="test-password",
            role="GROUND_STAFF",
        )

        cls.admin = User.objects.create_user(
            username="airport-admin",
            password="test-password",
            role="ADMIN",
        )

    def test_operator_only_sees_own_airline_flights(self):
        self.client.force_login(
            self.operator
        )

        response = self.client.get(
            reverse("flight_list")
        )

        self.assertContains(
            response,
            self.flight.flight_number,
        )

        self.assertNotContains(
            response,
            self.other_flight.flight_number,
        )

    def test_operator_cannot_open_other_airline_flight(self):
        self.client.force_login(
            self.operator
        )

        response = self.client.get(
            reverse(
                "flight_detail",
                args=[self.other_flight.id],
            )
        )

        self.assertEqual(
            response.status_code,
            404,
        )

    def test_unassigned_operator_sees_no_flights(self):
        self.client.force_login(
            self.operator_without_airline
        )

        response = self.client.get(
            reverse("flight_list")
        )

        self.assertNotContains(
            response,
            self.flight.flight_number,
        )

        self.assertNotContains(
            response,
            self.other_flight.flight_number,
        )

    def test_ground_staff_cannot_create_flight(self):
        self.client.force_login(
            self.ground_staff
        )

        response = self.client.get(
            reverse("flight_create")
        )

        self.assertEqual(
            response.status_code,
            403,
        )

    def test_status_change_rejects_get_request(self):
        self.client.force_login(
            self.admin
        )

        response = self.client.get(
            reverse(
                "flight_change_status",
                args=[self.flight.id],
            )
        )

        self.assertEqual(
            response.status_code,
            405,
        )

    def test_admin_can_change_flight_status(self):
        self.client.force_login(
            self.admin
        )

        response = self.client.post(
            reverse(
                "flight_change_status",
                args=[self.flight.id],
            ),
            {
                "status": "DELAYED",
            },
        )

        self.assertRedirects(
            response,
            reverse(
                "flight_detail",
                args=[self.flight.id],
            ),
        )

        self.flight.refresh_from_db()

        self.assertEqual(
            self.flight.status,
            "DELAYED",
        )