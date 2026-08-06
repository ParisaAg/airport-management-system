from datetime import timedelta

from django.contrib.auth import get_user_model
from django.http import response
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from notifications.models import Notification
from airlines.models import Airline
from airports.models import Airport, Gate, Terminal
from audit.models import AuditLog
from fleet.models import Aircraft, AircraftType

from .forms import FlightForm, GateAssignmentForm
from .models import Flight, GateAssignment
from .services import (
    InvalidFlightTransition,
    available_flight_status_choices,
    transition_flight_status,
)


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
        departure_time = timezone.now() + timedelta(days=1)

        arrival_time = departure_time + timedelta(hours=1)

        return {
            "flight_number": "ra100",
            "airline": self.airline.id,
            "aircraft": self.aircraft.id,
            "origin": self.origin.id,
            "destination": self.destination.id,
            "departure_time": departure_time.strftime("%Y-%m-%dT%H:%M"),
            "arrival_time": arrival_time.strftime("%Y-%m-%dT%H:%M"),
        }

    def test_status_is_not_form_editable(self):
        form = FlightForm()

        self.assertNotIn(
            "status",
            form.fields,
        )

    def test_flight_number_is_normalized(self):
        form = FlightForm(data=self.valid_form_data())

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

        data["arrival_time"] = data["departure_time"]

        form = FlightForm(data=data)

        self.assertFalse(form.is_valid())

        self.assertIn(
            "__all__",
            form.errors,
        )

    def test_operator_only_sees_own_aircraft(self):
        form = FlightForm(user=self.operator)

        aircraft_queryset = form.fields["aircraft"].queryset

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

        gate_queryset = form.fields["gate"].queryset

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

        departure_time = timezone.now() + timedelta(days=1)

        cls.terminal = Terminal.objects.create(
            airport=cls.origin,
            name="Terminal 1",
            code="T1",
        )

        cls.gate = Gate.objects.create(
            terminal=cls.terminal,
            name="Gate A1",
            code="A1",
            is_active=True,
        )

        cls.flight = Flight.objects.create(
            flight_number="RA100",
            airline=cls.airline,
            aircraft=cls.aircraft,
            origin=cls.origin,
            destination=cls.destination,
            departure_time=departure_time,
            arrival_time=(departure_time + timedelta(hours=1)),
        )

        cls.other_flight = Flight.objects.create(
            flight_number="OA200",
            airline=cls.other_airline,
            aircraft=cls.other_aircraft,
            origin=cls.origin,
            destination=cls.destination,
            departure_time=departure_time,
            arrival_time=(departure_time + timedelta(hours=1)),
        )

        cls.operator = User.objects.create_user(
            username="airline-operator",
            password="test-password",
            role="AIRLINE_OPERATOR",
            airline=cls.airline,
        )

        cls.operator_without_airline = User.objects.create_user(
            username="unassigned-operator",
            password="test-password",
            role="AIRLINE_OPERATOR",
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

    def test_gate_assignment_creates_audit_event(self):
        self.client.force_login(self.admin)

        response = self.client.post(
            reverse(
                "gate_assignment_create",
                args=[self.flight.id],
            ),
            {
                "gate": self.gate.id,
                "notes": "Primary departure gate",
            },
        )

        self.assertRedirects(
            response,
            reverse(
                "flight_detail",
                args=[self.flight.id],
            ),
        )

        assignment = GateAssignment.objects.get(
            flight=self.flight,
            gate=self.gate,
        )

        event = AuditLog.objects.get(
            entity_type=("flights.GateAssignment"),
            entity_id=str(assignment.id),
            action=AuditLog.Action.ASSIGN,
        )

        self.assertEqual(
            event.actor,
            self.admin,
        )

        self.assertEqual(
            event.changes["gate"]["to"],
            "A1",
        )

    def test_gate_release_creates_audit_event(self):
        assignment = GateAssignment.objects.create(
            flight=self.flight,
            gate=self.gate,
            status="ACTIVE",
        )

        self.client.force_login(self.admin)

        response = self.client.post(
            reverse(
                "gate_assignment_release",
                args=[assignment.id],
            )
        )

        self.assertRedirects(
            response,
            reverse(
                "flight_detail",
                args=[self.flight.id],
            ),
        )

        assignment.refresh_from_db()

        self.assertEqual(
            assignment.status,
            "RELEASED",
        )

        event = AuditLog.objects.get(
            entity_type=("flights.GateAssignment"),
            entity_id=str(assignment.id),
            action=AuditLog.Action.RELEASE,
        )

        self.assertEqual(
            event.actor,
            self.admin,
        )

        self.assertEqual(
            event.changes["status"],
            {
                "from": "ACTIVE",
                "to": "RELEASED",
            },
        )

    def test_operator_only_sees_own_airline_flights(self):
        self.client.force_login(self.operator)

        response = self.client.get(reverse("flight_list"))

        self.assertContains(
            response,
            self.flight.flight_number,
        )

        self.assertNotContains(
            response,
            self.other_flight.flight_number,
        )

    def test_operator_cannot_open_other_airline_flight(self):
        self.client.force_login(self.operator)

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
        self.client.force_login(self.operator_without_airline)

        response = self.client.get(reverse("flight_list"))

        self.assertNotContains(
            response,
            self.flight.flight_number,
        )

        self.assertNotContains(
            response,
            self.other_flight.flight_number,
        )

    def test_ground_staff_cannot_create_flight(self):
        self.client.force_login(self.ground_staff)

        response = self.client.get(reverse("flight_create"))

        self.assertEqual(
            response.status_code,
            403,
        )

    def test_status_change_rejects_get_request(self):
        self.client.force_login(self.admin)

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
        self.client.force_login(self.admin)

        response = self.client.post(
            reverse(
                "flight_change_status",
                args=[self.flight.id],
            ),
            {
                "status": "DELAYED",
                "delay_minutes": 45,
                "reason": "Adverse weather conditions",
            }
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

    def test_status_change_creates_audit_event(self):
        self.client.force_login(self.admin)

        self.client.post(
            reverse(
                "flight_change_status",
                args=[self.flight.id],
            ),
            {
                "status": "DELAYED",
                "delay_minutes": 45,
                "reason": "Adverse weather conditions",
            }
        )

        event = AuditLog.objects.get(
            entity_type="flights.Flight",
            entity_id=str(self.flight.id),
            action=(AuditLog.Action.STATUS_CHANGE),
        )

        self.assertEqual(
            event.actor,
            self.admin,
        )

        self.assertEqual(
            event.changes["status"],
            {
                "from": "SCHEDULED",
                "to": "DELAYED",
            },
        )
    def test_public_flight_board_is_accessible_without_login(self):
        response = self.client.get(
            reverse("public_flight_board"),
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertTemplateUsed(
            response,
            "flights/board.html",
        )

        self.assertContains(
            response,
            self.origin.name,
        )

    def test_public_departures_api_returns_matching_flights(self):
        response = self.client.get(
            reverse("public_flight_board_data"),
            {
                "airport": self.origin.iata_code,
                "type": "DEPARTURES",
            },
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        payload = response.json()

        self.assertEqual(
            payload["airport"]["iata_code"],
            self.origin.iata_code,
        )

        self.assertEqual(
            payload["board_type"],
            "DEPARTURES",
        )

        flight_numbers = {
            flight["flight_number"]
            for flight in payload["flights"]
        }

        self.assertIn(
            self.flight.flight_number,
            flight_numbers,
        )

        self.assertIn(
            self.other_flight.flight_number,
            flight_numbers,
        )

    def test_public_arrivals_api_returns_matching_flights(self):
        response = self.client.get(
            reverse("public_flight_board_data"),
            {
                "airport": self.destination.iata_code,
                "type": "ARRIVALS",
            },
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        payload = response.json()

        self.assertEqual(
            payload["board_type"],
            "ARRIVALS",
        )

        flight_numbers = {
            flight["flight_number"]
            for flight in payload["flights"]
        }

        self.assertIn(
            self.flight.flight_number,
            flight_numbers,
        )

    def test_public_board_api_rejects_unknown_airport(self):
        response = self.client.get(
            reverse("public_flight_board_data"),
            {
                "airport": "XXX",
                "type": "DEPARTURES",
            },
        )

        self.assertEqual(
            response.status_code,
            400,
        )

        self.assertEqual(
            response.json()["error"],
            "A valid airport IATA code is required.",
        )

    def test_public_board_api_defaults_invalid_type_to_departures(self):
        response = self.client.get(
            reverse("public_flight_board_data"),
            {
                "airport": self.origin.iata_code,
                "type": "INVALID",
            },
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertEqual(
            response.json()["board_type"],
            "DEPARTURES",
        )

    def test_public_board_excludes_flights_outside_time_window(self):
        departure_time = (
            timezone.now()
            + timedelta(days=7)
        )

        self.flight.departure_time = departure_time
        self.flight.arrival_time = (
            departure_time
            + timedelta(hours=1)
        )

        self.flight.save(
            update_fields=[
                "departure_time",
                "arrival_time",
            ],
        )

        response = self.client.get(
            reverse("public_flight_board_data"),
            {
                "airport": self.origin.iata_code,
                "type": "DEPARTURES",
            },
        )

        flight_numbers = {
            flight["flight_number"]
            for flight
            in response.json()["flights"]
        }

        self.assertNotIn(
            self.flight.flight_number,
            flight_numbers,
        )

    def test_public_board_api_includes_active_gate_information(self):
        GateAssignment.objects.create(
            flight=self.flight,
            gate=self.gate,
            status="ACTIVE",
        )

        response = self.client.get(
            reverse("public_flight_board_data"),
            {
                "airport": self.origin.iata_code,
                "type": "DEPARTURES",
            },
        )

        payload = response.json()

        flight_data = next(
            flight
            for flight in payload["flights"]
            if (
                flight["flight_number"]
                == self.flight.flight_number
            )
        )

        self.assertEqual(
            flight_data["gate"],
            self.gate.code,
        )

        self.assertEqual(
            flight_data["terminal"],
            self.terminal.code,
        )


    def test_public_board_uses_estimated_time_for_delayed_flight(self):
        transition_flight_status(
            flight_id=self.flight.id,
            new_status="DELAYED",
            delay_minutes=45,
            reason="Adverse weather conditions",
            actor=self.admin,
        )

        self.flight.refresh_from_db()

        response = self.client.get(
            reverse("public_flight_board_data"),
            {
                "airport": self.origin.iata_code,
                "type": "DEPARTURES",
            },
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        flight_data = next(
            item
            for item in response.json()["flights"]
            if (
                item["flight_number"]
                == self.flight.flight_number
            )
        )

        self.assertEqual(
            flight_data["display_time"],
            (
                self.flight
                .estimated_departure_time
                .isoformat()
            ),
        )

        self.assertEqual(
            flight_data["delay_minutes"],
            45,
        )

        self.assertEqual(
            flight_data["disruption_reason"],
            "Adverse weather conditions",
        )
    def test_delay_notifies_relevant_operational_users(self):
        passenger_service = User.objects.create_user(
            username="passenger-service",
            password="test-password",
            role="PASSENGER_SERVICE",
        )

        other_operator = User.objects.create_user(
            username="other-airline-operator",
            password="test-password",
            role="AIRLINE_OPERATOR",
            airline=self.other_airline,
        )

        transition_flight_status(
            flight_id=self.flight.id,
            new_status="DELAYED",
            delay_minutes=45,
            reason="Adverse weather conditions",
            actor=self.admin,
        )

        recipient_ids = set(
            Notification.objects.values_list(
                "user_id",
                flat=True,
            )
        )

        self.assertIn(
            self.operator.id,
            recipient_ids,
        )

        self.assertIn(
            self.ground_staff.id,
            recipient_ids,
        )

        self.assertIn(
            passenger_service.id,
            recipient_ids,
        )

        self.assertNotIn(
            other_operator.id,
            recipient_ids,
        )

        self.assertNotIn(
            self.operator_without_airline.id,
            recipient_ids,
        )

        self.assertNotIn(
            self.admin.id,
            recipient_ids,
        )

        self.assertTrue(
            Notification.objects.filter(
                notification_type="WARNING",
            ).exists()
        )

    def test_cancellation_notification_contains_reason(self):
        transition_flight_status(
            flight_id=self.flight.id,
            new_status="CANCELLED",
            reason=(
                "Aircraft technical "
                "inspection required"
            ),
            actor=self.admin,
        )

        notification = Notification.objects.get(
            user=self.ground_staff,
        )

        self.assertEqual(
            notification.notification_type,
            "ERROR",
        )

        self.assertIn(
            self.flight.flight_number,
            notification.title,
        )

        self.assertIn(
            (
                "Aircraft technical "
                "inspection required"
            ),
            notification.message,
        )

    def test_normal_status_change_does_not_create_disruption_notification(
        self,
    ):
        transition_flight_status(
            flight_id=self.flight.id,
            new_status="BOARDING",
            actor=self.admin,
        )

        self.assertFalse(
            Notification.objects.exists()
        )
class FlightTransitionTests(TestCase):
    
    @classmethod
    def setUpTestData(cls):
        airline = Airline.objects.create(
            name="Workflow Air",
            iata_code="WA",
            icao_code="WFA",
            country="Iran",
        )

        aircraft_type = AircraftType.objects.create(
            manufacturer="Airbus",
            model="A319",
            passenger_capacity=150,
            range_km=6900,
        )

        aircraft = Aircraft.objects.create(
            airline=airline,
            aircraft_type=aircraft_type,
            registration_number="EP-WFA",
        )

        origin = Airport.objects.create(
            name="Imam Khomeini International Airport",
            icao_code="OIIE",
            iata_code="IKA",
            country="Iran",
            city="Tehran",
        )

        destination = Airport.objects.create(
            name="Shiraz International Airport",
            icao_code="OISS",
            iata_code="SYZ",
            country="Iran",
            city="Shiraz",
        )

        departure_time = timezone.now() + timedelta(days=1)

        cls.flight = Flight.objects.create(
            flight_number="WA300",
            airline=airline,
            aircraft=aircraft,
            origin=origin,
            destination=destination,
            departure_time=departure_time,
            arrival_time=(departure_time + timedelta(hours=1)),
            status="SCHEDULED",
        )

    def test_scheduled_flight_can_begin_boarding(self):
        flight = transition_flight_status(
            flight_id=self.flight.id,
            new_status="BOARDING",
        )

        self.assertEqual(
            flight.status,
            "BOARDING",
        )

    def test_scheduled_flight_cannot_depart_directly(self):
        with self.assertRaises(InvalidFlightTransition):
            transition_flight_status(
                flight_id=self.flight.id,
                new_status="DEPARTED",
            )

        self.flight.refresh_from_db()

        self.assertEqual(
            self.flight.status,
            "SCHEDULED",
        )

    def test_flight_can_complete_valid_lifecycle(self):
        transition_flight_status(
            flight_id=self.flight.id,
            new_status="BOARDING",
        )

        transition_flight_status(
            flight_id=self.flight.id,
            new_status="DEPARTED",
        )

        flight = transition_flight_status(
            flight_id=self.flight.id,
            new_status="ARRIVED",
        )

        self.assertEqual(
            flight.status,
            "ARRIVED",
        )

    def test_arrived_flight_is_terminal(self):
        transition_flight_status(
            flight_id=self.flight.id,
            new_status="BOARDING",
        )

        transition_flight_status(
            flight_id=self.flight.id,
            new_status="DEPARTED",
        )

        transition_flight_status(
            flight_id=self.flight.id,
            new_status="ARRIVED",
        )

        with self.assertRaises(InvalidFlightTransition):
            transition_flight_status(
                flight_id=self.flight.id,
                new_status="DELAYED",
            )

    def test_available_choices_only_include_valid_transitions(self):
        choices = dict(available_flight_status_choices("SCHEDULED"))

        self.assertIn(
            "BOARDING",
            choices,
        )

        self.assertIn(
            "DELAYED",
            choices,
        )

        self.assertIn(
            "CANCELLED",
            choices,
        )

        self.assertNotIn(
            "DEPARTED",
            choices,
        )

        self.assertNotIn(
            "ARRIVED",
            choices,
        )
