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

from .models import PassengerRequest
from .services import (
    assign_passenger_request,
    transition_passenger_request_status,
)


User = get_user_model()


class PassengerServiceAuthorizationTests(
    TestCase
):

    @classmethod
    def setUpTestData(cls):
        cls.airline = Airline.objects.create(
            name="Passenger View Airlines",
            iata_code="PV",
            icao_code="PSV",
            country="Iran",
        )

        cls.aircraft_type = (
            AircraftType.objects.create(
                manufacturer="Airbus",
                model="A320 Passenger View",
                passenger_capacity=180,
                range_km=6100,
            )
        )

        cls.aircraft = Aircraft.objects.create(
            airline=cls.airline,
            aircraft_type=cls.aircraft_type,
            registration_number="EP-PSV",
        )

        cls.origin = Airport.objects.create(
            name="Passenger View Origin",
            icao_code="OIPV",
            iata_code="PVO",
            country="Iran",
            city="Tehran",
        )

        cls.destination = Airport.objects.create(
            name="Passenger View Destination",
            icao_code="OIDV",
            iata_code="PVD",
            country="Iran",
            city="Mashhad",
        )

        departure_time = (
            timezone.now()
            + timedelta(days=1)
        )

        cls.flight = Flight.objects.create(
            flight_number="PV701",
            airline=cls.airline,
            aircraft=cls.aircraft,
            origin=cls.origin,
            destination=cls.destination,
            departure_time=departure_time,
            arrival_time=(
                departure_time
                + timedelta(hours=1)
            ),
        )

        cls.admin = User.objects.create_user(
            username="passenger-view-admin",
            password="test-password",
            role="ADMIN",
        )

        cls.manager = User.objects.create_user(
            username="passenger-view-manager",
            password="test-password",
            role="AIRPORT_MANAGER",
        )

        cls.passenger_agent = (
            User.objects.create_user(
                username="passenger-view-agent",
                password="test-password",
                role="PASSENGER_SERVICE",
            )
        )

        cls.second_agent = (
            User.objects.create_user(
                username="passenger-view-agent-two",
                password="test-password",
                role="PASSENGER_SERVICE",
            )
        )

        cls.ground_staff = (
            User.objects.create_user(
                username="passenger-view-ground",
                password="test-password",
                role="GROUND_STAFF",
            )
        )

        cls.viewer = User.objects.create_user(
            username="passenger-viewer",
            password="test-password",
            role="VIEWER",
        )

        passenger_request = (
            PassengerRequest.objects.create(
                flight=cls.flight,
                passenger_name="Mina Hosseini",
                booking_reference="ABC701",
                request_type="WHEELCHAIR",
                priority="HIGH",
                service_location=(
                    "Terminal 1 / Check-in"
                ),
                description=(
                    "Passenger requires mobility "
                    "assistance before departure."
                ),
            )
        )

        cls.request_id = (
            passenger_request.id
        )

    def setUp(self):
        self.passenger_request = (
            PassengerRequest.objects.get(
                pk=self.request_id
            )
        )

    def test_anonymous_user_is_redirected_to_login(
        self,
    ):
        response = self.client.get(
            reverse(
                "passenger_service:list"
            )
        )

        expected_url = (
            f"{reverse('login')}"
            f"?next="
            f"{reverse('passenger_service:list')}"
        )

        self.assertRedirects(
            response,
            expected_url,
        )

    def test_admin_can_access_passenger_center(
        self,
    ):
        self.client.force_login(
            self.admin
        )

        response = self.client.get(
            reverse(
                "passenger_service:list"
            )
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertContains(
            response,
            self.passenger_request.reference,
        )

    def test_passenger_agent_can_access_center(
        self,
    ):
        self.client.force_login(
            self.passenger_agent
        )

        response = self.client.get(
            reverse(
                "passenger_service:list"
            )
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
            reverse(
                "passenger_service:list"
            )
        )

        detail_response = self.client.get(
            reverse(
                "passenger_service:detail",
                args=[
                    self.passenger_request.id,
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

    def test_viewer_cannot_access_passenger_center(
        self,
    ):
        self.client.force_login(
            self.viewer
        )

        response = self.client.get(
            reverse(
                "passenger_service:list"
            )
        )

        self.assertEqual(
            response.status_code,
            403,
        )

    def test_ground_staff_cannot_access_passenger_center(
        self,
    ):
        self.client.force_login(
            self.ground_staff
        )

        response = self.client.get(
            reverse(
                "passenger_service:list"
            )
        )

        self.assertEqual(
            response.status_code,
            403,
        )

    def test_airport_manager_cannot_create_request(
        self,
    ):
        self.client.force_login(
            self.manager
        )

        response = self.client.get(
            reverse(
                "passenger_service:create"
            )
        )

        self.assertEqual(
            response.status_code,
            403,
        )

    def test_passenger_agent_can_open_create_page(
        self,
    ):
        self.client.force_login(
            self.passenger_agent
        )

        response = self.client.get(
            reverse(
                "passenger_service:create"
            )
        )

        self.assertEqual(
            response.status_code,
            200,
        )

    def test_admin_can_create_passenger_request(
        self,
    ):
        self.client.force_login(
            self.admin
        )

        response = self.client.post(
            reverse(
                "passenger_service:create"
            ),
            {
                "flight": self.flight.id,
                "passenger_name": (
                    "Sara Ahmadi"
                ),
                "booking_reference": (
                    "xyz900"
                ),
                "request_type": (
                    "SPECIAL_ASSISTANCE"
                ),
                "priority": "URGENT",
                "service_location": (
                    "Departure Hall"
                ),
                "description": (
                    "Passenger requires "
                    "immediate assistance."
                ),
            },
        )

        passenger_request = (
            PassengerRequest.objects.get(
                passenger_name=(
                    "Sara Ahmadi"
                )
            )
        )

        self.assertRedirects(
            response,
            reverse(
                "passenger_service:detail",
                args=[
                    passenger_request.id,
                ],
            ),
        )

        self.assertEqual(
            passenger_request.status,
            "OPEN",
        )

        self.assertEqual(
            passenger_request
            .booking_reference,
            "XYZ900",
        )

        self.assertTrue(
            AuditLog.objects.filter(
                actor=self.admin,
                action=(
                    AuditLog.Action.CREATE
                ),
                entity_id=str(
                    passenger_request.id
                ),
            ).exists()
        )

    def test_invalid_create_data_does_not_create_request(
        self,
    ):
        self.client.force_login(
            self.admin
        )

        response = self.client.post(
            reverse(
                "passenger_service:create"
            ),
            {
                "flight": "",
                "passenger_name": "",
                "booking_reference": "",
                "request_type": "",
                "priority": "",
                "service_location": "",
                "description": "",
            },
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertEqual(
            PassengerRequest.objects.count(),
            1,
        )

    def test_airport_manager_cannot_assign_request(
        self,
    ):
        self.client.force_login(
            self.manager
        )

        response = self.client.post(
            reverse(
                "passenger_service:assign",
                args=[
                    self.passenger_request.id,
                ],
            ),
            {
                "staff": (
                    self.passenger_agent.id
                ),
            },
        )

        self.assertEqual(
            response.status_code,
            403,
        )

        self.passenger_request.refresh_from_db()

        self.assertIsNone(
            self.passenger_request
            .assigned_staff
        )

    def test_passenger_agent_can_assign_request(
        self,
    ):
        self.client.force_login(
            self.passenger_agent
        )

        response = self.client.post(
            reverse(
                "passenger_service:assign",
                args=[
                    self.passenger_request.id,
                ],
            ),
            {
                "staff": (
                    self.passenger_agent.id
                ),
            },
        )

        self.assertRedirects(
            response,
            reverse(
                "passenger_service:detail",
                args=[
                    self.passenger_request.id,
                ],
            ),
        )

        self.passenger_request.refresh_from_db()

        self.assertEqual(
            self.passenger_request
            .assigned_staff,
            self.passenger_agent,
        )

        self.assertEqual(
            self.passenger_request.status,
            "ASSIGNED",
        )

        self.assertTrue(
            AuditLog.objects.filter(
                actor=self.passenger_agent,
                action=AuditLog.Action.ASSIGN,
                entity_id=str(
                    self.passenger_request.id
                ),
            ).exists()
        )

    def test_assignment_endpoint_rejects_get(
        self,
    ):
        self.client.force_login(
            self.admin
        )

        response = self.client.get(
            reverse(
                "passenger_service:assign",
                args=[
                    self.passenger_request.id,
                ],
            )
        )

        self.assertEqual(
            response.status_code,
            405,
        )

    def test_status_endpoint_rejects_get(
        self,
    ):
        self.client.force_login(
            self.admin
        )

        response = self.client.get(
            reverse(
                "passenger_service:change_status",
                args=[
                    self.passenger_request.id,
                ],
            )
        )

        self.assertEqual(
            response.status_code,
            405,
        )

    def test_assigned_agent_can_start_service(
        self,
    ):
        assign_passenger_request(
            request_id=(
                self.passenger_request.id
            ),
            staff=self.passenger_agent,
            actor=self.admin,
        )

        self.client.force_login(
            self.passenger_agent
        )

        response = self.client.post(
            reverse(
                "passenger_service:change_status",
                args=[
                    self.passenger_request.id,
                ],
            ),
            {
                "status": "IN_PROGRESS",
            },
        )

        self.assertRedirects(
            response,
            reverse(
                "passenger_service:detail",
                args=[
                    self.passenger_request.id,
                ],
            ),
        )

        self.passenger_request.refresh_from_db()

        self.assertEqual(
            self.passenger_request.status,
            "IN_PROGRESS",
        )

    def test_unassigned_passenger_agent_cannot_change_status(
        self,
    ):
        assign_passenger_request(
            request_id=(
                self.passenger_request.id
            ),
            staff=self.passenger_agent,
            actor=self.admin,
        )

        self.client.force_login(
            self.second_agent
        )

        response = self.client.post(
            reverse(
                "passenger_service:change_status",
                args=[
                    self.passenger_request.id,
                ],
            ),
            {
                "status": "IN_PROGRESS",
            },
        )

        self.assertEqual(
            response.status_code,
            403,
        )

        self.passenger_request.refresh_from_db()

        self.assertEqual(
            self.passenger_request.status,
            "ASSIGNED",
        )

    def test_airport_manager_cannot_change_status(
        self,
    ):
        assign_passenger_request(
            request_id=(
                self.passenger_request.id
            ),
            staff=self.passenger_agent,
            actor=self.admin,
        )

        self.client.force_login(
            self.manager
        )

        response = self.client.post(
            reverse(
                "passenger_service:change_status",
                args=[
                    self.passenger_request.id,
                ],
            ),
            {
                "status": "IN_PROGRESS",
            },
        )

        self.assertEqual(
            response.status_code,
            403,
        )

    def test_assigned_agent_can_complete_request(
        self,
    ):
        assign_passenger_request(
            request_id=(
                self.passenger_request.id
            ),
            staff=self.passenger_agent,
            actor=self.admin,
        )

        transition_passenger_request_status(
            request_id=(
                self.passenger_request.id
            ),
            new_status="IN_PROGRESS",
            actor=self.passenger_agent,
        )

        self.client.force_login(
            self.passenger_agent
        )

        response = self.client.post(
            reverse(
                "passenger_service:change_status",
                args=[
                    self.passenger_request.id,
                ],
            ),
            {
                "status": "COMPLETED",
                "resolution_notes": (
                    "Passenger was assisted "
                    "to the boarding gate."
                ),
            },
        )

        self.assertRedirects(
            response,
            reverse(
                "passenger_service:detail",
                args=[
                    self.passenger_request.id,
                ],
            ),
        )

        self.passenger_request.refresh_from_db()

        self.assertEqual(
            self.passenger_request.status,
            "COMPLETED",
        )

        self.assertEqual(
            self.passenger_request
            .resolution_notes,
            (
                "Passenger was assisted "
                "to the boarding gate."
            ),
        )

        self.assertIsNotNone(
            self.passenger_request
            .completed_at
        )

    def test_search_filters_passenger_requests(
        self,
    ):
        PassengerRequest.objects.create(
            flight=self.flight,
            passenger_name="Other Passenger",
            booking_reference="OTHER1",
            request_type="COMPLAINT",
            priority="LOW",
            service_location=(
                "Remote Service Desk"
            ),
            description=(
                "Unrelated passenger request."
            ),
        )

        self.client.force_login(
            self.admin
        )

        response = self.client.get(
            reverse(
                "passenger_service:list"
            ),
            {
                "search": "Mina Hosseini",
            },
        )

        self.assertContains(
            response,
            self.passenger_request.reference,
        )

        self.assertNotContains(
            response,
            "Remote Service Desk",
        )

    def test_unassigned_filter_excludes_assigned_requests(
        self,
    ):
        assigned_request = (
            PassengerRequest.objects.create(
                flight=self.flight,
                passenger_name=(
                    "Assigned Passenger"
                ),
                request_type=(
                    "LOST_FOUND"
                ),
                priority="MEDIUM",
                service_location=(
                    "Arrival Hall"
                ),
                description=(
                    "Assigned lost property "
                    "request."
                ),
            )
        )

        assign_passenger_request(
            request_id=(
                assigned_request.id
            ),
            staff=self.passenger_agent,
            actor=self.admin,
        )

        self.client.force_login(
            self.admin
        )

        response = self.client.get(
            reverse(
                "passenger_service:list"
            ),
            {
                "assignment": "UNASSIGNED",
            },
        )

        self.assertContains(
            response,
            self.passenger_request.reference,
        )

        self.assertNotContains(
            response,
            assigned_request.reference,
        )

    def test_assigned_to_me_filter_returns_own_requests(
        self,
    ):
        own_request = (
            PassengerRequest.objects.create(
                flight=self.flight,
                passenger_name=(
                    "Own Passenger"
                ),
                request_type=(
                    "SPECIAL_ASSISTANCE"
                ),
                priority="HIGH",
                service_location=(
                    "Gate B2"
                ),
                description=(
                    "Own assigned request."
                ),
            )
        )

        other_request = (
            PassengerRequest.objects.create(
                flight=self.flight,
                passenger_name=(
                    "Other Assigned Passenger"
                ),
                request_type="OTHER",
                priority="LOW",
                service_location=(
                    "Terminal Office"
                ),
                description=(
                    "Other assigned request."
                ),
            )
        )

        assign_passenger_request(
            request_id=own_request.id,
            staff=self.passenger_agent,
            actor=self.admin,
        )

        assign_passenger_request(
            request_id=other_request.id,
            staff=self.second_agent,
            actor=self.admin,
        )

        self.client.force_login(
            self.passenger_agent
        )

        response = self.client.get(
            reverse(
                "passenger_service:list"
            ),
            {
                "assignment": "MINE",
            },
        )

        self.assertContains(
            response,
            own_request.reference,
        )

        self.assertNotContains(
            response,
            other_request.reference,
        )