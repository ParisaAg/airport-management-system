from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

from airlines.models import Airline
from airports.models import Airport
from audit.models import AuditLog
from fleet.models import Aircraft, AircraftType
from flights.models import Flight

from .models import PassengerRequest
from .services import (
    InvalidPassengerAssignment,
    InvalidPassengerTransition,
    assign_passenger_request,
    available_passenger_status_choices,
    transition_passenger_request_status,
)


User = get_user_model()


class PassengerRequestWorkflowTests(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.airline = Airline.objects.create(
            name="Passenger Test Airlines",
            iata_code="PT",
            icao_code="PST",
            country="Iran",
        )

        cls.aircraft_type = AircraftType.objects.create(
            manufacturer="Airbus",
            model="A321 Passenger Test",
            passenger_capacity=190,
            range_km=5900,
        )

        cls.aircraft = Aircraft.objects.create(
            airline=cls.airline,
            aircraft_type=cls.aircraft_type,
            registration_number="EP-PSR",
        )

        cls.origin = Airport.objects.create(
            name="Passenger Origin Airport",
            icao_code="OIPT",
            iata_code="POT",
            country="Iran",
            city="Tehran",
        )

        cls.destination = Airport.objects.create(
            name="Passenger Destination Airport",
            icao_code="OIPS",
            iata_code="PDT",
            country="Iran",
            city="Mashhad",
        )

        departure_time = (
            timezone.now()
            + timedelta(days=1)
        )

        cls.flight = Flight.objects.create(
            flight_number="PT501",
            airline=cls.airline,
            aircraft=cls.aircraft,
            origin=cls.origin,
            destination=cls.destination,
            departure_time=departure_time,
            arrival_time=(
                departure_time
                + timedelta(
                    hours=1,
                    minutes=20,
                )
            ),
        )

        cls.admin = User.objects.create_user(
            username="passenger-admin",
            password="test-password",
            role="ADMIN",
        )

        cls.passenger_staff = (
            User.objects.create_user(
                username="passenger-agent",
                password="test-password",
                role="PASSENGER_SERVICE",
            )
        )

        cls.second_passenger_staff = (
            User.objects.create_user(
                username="passenger-agent-two",
                password="test-password",
                role="PASSENGER_SERVICE",
            )
        )

        cls.ground_staff = (
            User.objects.create_user(
                username="passenger-ground",
                password="test-password",
                role="GROUND_STAFF",
            )
        )

    def setUp(self):
        self.passenger_request = (
            PassengerRequest.objects.create(
                flight=self.flight,
                passenger_name="Sara Ahmadi",
                booking_reference="ABC123",
                request_type="WHEELCHAIR",
                priority="HIGH",
                service_location=(
                    "Terminal 1 / Check-in"
                ),
                description=(
                    "Passenger requires "
                    "wheelchair assistance "
                    "before boarding."
                ),
            )
        )

    def test_reference_uses_passenger_prefix(
        self,
    ):
        self.assertEqual(
            self.passenger_request.reference,
            (
                f"PSR-"
                f"{self.passenger_request.pk:06d}"
            ),
        )

    def test_new_request_is_active(
        self,
    ):
        self.assertEqual(
            self.passenger_request.status,
            "OPEN",
        )

        self.assertTrue(
            self.passenger_request.is_active
        )

    def test_open_request_has_expected_transitions(
        self,
    ):
        choices = dict(
            available_passenger_status_choices(
                "OPEN"
            )
        )

        self.assertIn(
            "ASSIGNED",
            choices,
        )

        self.assertIn(
            "CANCELLED",
            choices,
        )

        self.assertNotIn(
            "COMPLETED",
            choices,
        )

    def test_request_can_be_assigned_to_passenger_staff(
        self,
    ):
        passenger_request = (
            assign_passenger_request(
                request_id=(
                    self.passenger_request.id
                ),
                staff=self.passenger_staff,
                actor=self.admin,
            )
        )

        self.assertEqual(
            passenger_request.assigned_staff,
            self.passenger_staff,
        )

        self.assertEqual(
            passenger_request.status,
            "ASSIGNED",
        )

        self.assertTrue(
            AuditLog.objects.filter(
                actor=self.admin,
                action=AuditLog.Action.ASSIGN,
                entity_id=str(
                    passenger_request.id
                ),
            ).exists()
        )

    def test_non_passenger_staff_cannot_be_assigned(
        self,
    ):
        with self.assertRaises(
            InvalidPassengerAssignment
        ):
            assign_passenger_request(
                request_id=(
                    self.passenger_request.id
                ),
                staff=self.ground_staff,
                actor=self.admin,
            )

        self.passenger_request.refresh_from_db()

        self.assertIsNone(
            self.passenger_request.assigned_staff
        )

        self.assertEqual(
            self.passenger_request.status,
            "OPEN",
        )

    def test_inactive_passenger_staff_cannot_be_assigned(
        self,
    ):
        self.passenger_staff.is_active = False

        self.passenger_staff.save(
            update_fields=[
                "is_active",
            ]
        )

        with self.assertRaises(
            InvalidPassengerAssignment
        ):
            assign_passenger_request(
                request_id=(
                    self.passenger_request.id
                ),
                staff=self.passenger_staff,
                actor=self.admin,
            )

    def test_assigned_request_can_start_progress(
        self,
    ):
        assign_passenger_request(
            request_id=(
                self.passenger_request.id
            ),
            staff=self.passenger_staff,
            actor=self.admin,
        )

        passenger_request = (
            transition_passenger_request_status(
                request_id=(
                    self.passenger_request.id
                ),
                new_status="IN_PROGRESS",
                actor=self.passenger_staff,
            )
        )

        self.assertEqual(
            passenger_request.status,
            "IN_PROGRESS",
        )

        self.assertTrue(
            AuditLog.objects.filter(
                actor=self.passenger_staff,
                action=(
                    AuditLog.Action.STATUS_CHANGE
                ),
                entity_id=str(
                    passenger_request.id
                ),
            ).exists()
        )

    def test_open_request_cannot_start_progress_directly(
        self,
    ):
        with self.assertRaises(
            InvalidPassengerTransition
        ):
            transition_passenger_request_status(
                request_id=(
                    self.passenger_request.id
                ),
                new_status="IN_PROGRESS",
                actor=self.admin,
            )

        self.passenger_request.refresh_from_db()

        self.assertEqual(
            self.passenger_request.status,
            "OPEN",
        )

    def test_request_cannot_complete_before_in_progress(
        self,
    ):
        assign_passenger_request(
            request_id=(
                self.passenger_request.id
            ),
            staff=self.passenger_staff,
            actor=self.admin,
        )

        with self.assertRaises(
            InvalidPassengerTransition
        ):
            transition_passenger_request_status(
                request_id=(
                    self.passenger_request.id
                ),
                new_status="COMPLETED",
                actor=self.passenger_staff,
                resolution_notes=(
                    "Passenger assisted."
                ),
            )

    def test_completion_requires_resolution_notes(
        self,
    ):
        assign_passenger_request(
            request_id=(
                self.passenger_request.id
            ),
            staff=self.passenger_staff,
            actor=self.admin,
        )

        transition_passenger_request_status(
            request_id=(
                self.passenger_request.id
            ),
            new_status="IN_PROGRESS",
            actor=self.passenger_staff,
        )

        with self.assertRaises(
            InvalidPassengerTransition
        ):
            transition_passenger_request_status(
                request_id=(
                    self.passenger_request.id
                ),
                new_status="COMPLETED",
                actor=self.passenger_staff,
                resolution_notes="",
            )

    def test_in_progress_request_can_be_completed(
        self,
    ):
        assign_passenger_request(
            request_id=(
                self.passenger_request.id
            ),
            staff=self.passenger_staff,
            actor=self.admin,
        )

        transition_passenger_request_status(
            request_id=(
                self.passenger_request.id
            ),
            new_status="IN_PROGRESS",
            actor=self.passenger_staff,
        )

        passenger_request = (
            transition_passenger_request_status(
                request_id=(
                    self.passenger_request.id
                ),
                new_status="COMPLETED",
                actor=self.passenger_staff,
                resolution_notes=(
                    "Passenger was assisted "
                    "to the boarding gate."
                ),
            )
        )

        self.assertEqual(
            passenger_request.status,
            "COMPLETED",
        )

        self.assertEqual(
            passenger_request.resolution_notes,
            (
                "Passenger was assisted "
                "to the boarding gate."
            ),
        )

        self.assertIsNotNone(
            passenger_request.completed_at
        )

        self.assertFalse(
            passenger_request.is_active
        )

        self.assertTrue(
            AuditLog.objects.filter(
                actor=self.passenger_staff,
                action=(
                    AuditLog.Action.STATUS_CHANGE
                ),
                entity_id=str(
                    passenger_request.id
                ),
            ).exists()
        )

    def test_open_request_can_be_cancelled(
        self,
    ):
        passenger_request = (
            transition_passenger_request_status(
                request_id=(
                    self.passenger_request.id
                ),
                new_status="CANCELLED",
                actor=self.admin,
            )
        )

        self.assertEqual(
            passenger_request.status,
            "CANCELLED",
        )

        self.assertFalse(
            passenger_request.is_active
        )

    def test_completed_request_is_terminal(
        self,
    ):
        assign_passenger_request(
            request_id=(
                self.passenger_request.id
            ),
            staff=self.passenger_staff,
            actor=self.admin,
        )

        transition_passenger_request_status(
            request_id=(
                self.passenger_request.id
            ),
            new_status="IN_PROGRESS",
            actor=self.passenger_staff,
        )

        transition_passenger_request_status(
            request_id=(
                self.passenger_request.id
            ),
            new_status="COMPLETED",
            actor=self.passenger_staff,
            resolution_notes=(
                "Service completed."
            ),
        )

        with self.assertRaises(
            InvalidPassengerTransition
        ):
            transition_passenger_request_status(
                request_id=(
                    self.passenger_request.id
                ),
                new_status="OPEN",
                actor=self.admin,
            )

    def test_cancelled_request_cannot_be_reassigned(
        self,
    ):
        transition_passenger_request_status(
            request_id=(
                self.passenger_request.id
            ),
            new_status="CANCELLED",
            actor=self.admin,
        )

        with self.assertRaises(
            InvalidPassengerAssignment
        ):
            assign_passenger_request(
                request_id=(
                    self.passenger_request.id
                ),
                staff=(
                    self.second_passenger_staff
                ),
                actor=self.admin,
            )

    def test_request_can_be_reassigned_while_active(
        self,
    ):
        assign_passenger_request(
            request_id=(
                self.passenger_request.id
            ),
            staff=self.passenger_staff,
            actor=self.admin,
        )

        passenger_request = (
            assign_passenger_request(
                request_id=(
                    self.passenger_request.id
                ),
                staff=(
                    self.second_passenger_staff
                ),
                actor=self.admin,
            )
        )

        self.assertEqual(
            passenger_request.assigned_staff,
            self.second_passenger_staff,
        )

        self.assertEqual(
            passenger_request.status,
            "ASSIGNED",
        )