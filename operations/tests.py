from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from airlines.models import Airline
from airports.models import Airport
from fleet.models import Aircraft, AircraftType
from flights.models import Flight

from .models import GroundOperation, OperationType
from .services import (
    InvalidOperationTransition,
    transition_ground_operation,
)


User = get_user_model()


class GroundOperationTestData(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.airline = Airline.objects.create(
            name="Resume Air",
            iata_code="RA",
            icao_code="RSA",
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

        departure_time = (
            timezone.now() + timedelta(days=1)
        )

        cls.flight = Flight.objects.create(
            flight_number="RA100",
            airline=cls.airline,
            aircraft=cls.aircraft,
            origin=cls.origin,
            destination=cls.destination,
            departure_time=departure_time,
            arrival_time=(
                departure_time + timedelta(hours=1)
            ),
        )

        cls.fueling_type = OperationType.objects.create(
            name="Refueling",
        )

        cls.cleaning_type = OperationType.objects.create(
            name="Cabin Cleaning",
        )

        cls.admin = User.objects.create_user(
            username="airport-admin",
            password="test-password",
            role="ADMIN",
        )

        cls.manager = User.objects.create_user(
            username="airport-manager",
            password="test-password",
            role="AIRPORT_MANAGER",
        )

        cls.ground_staff = User.objects.create_user(
            username="ground-staff",
            password="test-password",
            role="GROUND_STAFF",
        )

        cls.other_ground_staff = User.objects.create_user(
            username="other-ground-staff",
            password="test-password",
            role="GROUND_STAFF",
        )

        cls.operation = GroundOperation.objects.create(
            flight=cls.flight,
            operation_type=cls.fueling_type,
            assigned_staff=cls.ground_staff,
            status="PENDING",
        )

        cls.other_operation = GroundOperation.objects.create(
            flight=cls.flight,
            operation_type=cls.cleaning_type,
            assigned_staff=cls.other_ground_staff,
            status="PENDING",
        )


class GroundOperationTransitionTests(
    GroundOperationTestData
):
    def test_pending_operation_can_start(self):
        operation = transition_ground_operation(
            operation_id=self.operation.id,
            new_status="IN_PROGRESS",
        )

        self.assertEqual(
            operation.status,
            "IN_PROGRESS",
        )

        self.assertIsNotNone(
            operation.start_time,
        )

    def test_in_progress_operation_can_complete(self):
        transition_ground_operation(
            operation_id=self.operation.id,
            new_status="IN_PROGRESS",
        )

        operation = transition_ground_operation(
            operation_id=self.operation.id,
            new_status="COMPLETED",
        )

        self.assertEqual(
            operation.status,
            "COMPLETED",
        )

        self.assertIsNotNone(
            operation.end_time,
        )

    def test_pending_operation_cannot_complete_directly(self):
        with self.assertRaises(
            InvalidOperationTransition
        ):
            transition_ground_operation(
                operation_id=self.operation.id,
                new_status="COMPLETED",
            )

        self.operation.refresh_from_db()

        self.assertEqual(
            self.operation.status,
            "PENDING",
        )

    def test_completed_operation_is_terminal(self):
        transition_ground_operation(
            operation_id=self.operation.id,
            new_status="IN_PROGRESS",
        )

        transition_ground_operation(
            operation_id=self.operation.id,
            new_status="COMPLETED",
        )

        with self.assertRaises(
            InvalidOperationTransition
        ):
            transition_ground_operation(
                operation_id=self.operation.id,
                new_status="CANCELLED",
            )


class GroundOperationAuthorizationTests(
    GroundOperationTestData
):
    def test_ground_staff_only_sees_assigned_operations(self):
        self.client.force_login(
            self.ground_staff
        )

        response = self.client.get(
            reverse("ground_operation_list")
        )

        self.assertContains(
            response,
            self.fueling_type.name,
        )

        self.assertNotContains(
            response,
            self.cleaning_type.name,
        )

    def test_ground_staff_cannot_create_operation(self):
        self.client.force_login(
            self.ground_staff
        )

        response = self.client.get(
            reverse("ground_operation_create")
        )

        self.assertEqual(
            response.status_code,
            403,
        )

    def test_airport_manager_can_open_create_page(self):
        self.client.force_login(
            self.manager
        )

        response = self.client.get(
            reverse("ground_operation_create")
        )

        self.assertEqual(
            response.status_code,
            200,
        )

    def test_status_change_rejects_get_request(self):
        self.client.force_login(
            self.ground_staff
        )

        response = self.client.get(
            reverse(
                "ground_operation_change_status",
                args=[self.operation.id],
            )
        )

        self.assertEqual(
            response.status_code,
            405,
        )

    def test_ground_staff_cannot_update_other_operation(self):
        self.client.force_login(
            self.ground_staff
        )

        response = self.client.post(
            reverse(
                "ground_operation_change_status",
                args=[self.other_operation.id],
            ),
            {
                "status": "IN_PROGRESS",
            },
        )

        self.assertEqual(
            response.status_code,
            404,
        )

    def test_ground_staff_can_start_assigned_operation(self):
        self.client.force_login(
            self.ground_staff
        )

        response = self.client.post(
            reverse(
                "ground_operation_change_status",
                args=[self.operation.id],
            ),
            {
                "status": "IN_PROGRESS",
            },
        )

        self.assertRedirects(
            response,
            reverse("ground_operation_list"),
        )

        self.operation.refresh_from_db()

        self.assertEqual(
            self.operation.status,
            "IN_PROGRESS",
        )