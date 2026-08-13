from types import SimpleNamespace

from django.contrib.auth import get_user_model
from django.test import TestCase

from .models import Notification
from .services import (
    create_notifications,
    notify_critical_security_report,
    notify_ground_operation_completed,
    notify_urgent_passenger_request,
)


User = get_user_model()


class NotificationServiceTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.admin = User.objects.create_user(
            username="notification-admin",
            password="test-password",
            role="ADMIN",
        )

        cls.manager = User.objects.create_user(
            username="notification-manager",
            password="test-password",
            role="AIRPORT_MANAGER",
        )

        cls.ground_staff = User.objects.create_user(
            username="notification-ground",
            password="test-password",
            role="GROUND_STAFF",
        )

        cls.security_officer = (
            User.objects.create_user(
                username="notification-security",
                password="test-password",
                role="SECURITY_OFFICER",
            )
        )

        cls.passenger_staff = (
            User.objects.create_user(
                username="notification-passenger",
                password="test-password",
                role="PASSENGER_SERVICE",
            )
        )

        cls.airline_operator = (
            User.objects.create_user(
                username="notification-operator",
                password="test-password",
                role="AIRLINE_OPERATOR",
            )
        )

        cls.inactive_admin = (
            User.objects.create_user(
                username="inactive-admin",
                password="test-password",
                role="ADMIN",
                is_active=False,
            )
        )

    def recipient_ids(self):
        return set(
            Notification.objects.values_list(
                "user_id",
                flat=True,
            )
        )

    def test_create_notifications_excludes_actor_and_inactive_users(
        self,
    ):
        recipients = User.objects.filter(
            role="ADMIN",
        )

        created_count = create_notifications(
            recipients=recipients,
            title="Operational event",
            message="An operational event occurred.",
            notification_type="INFO",
            actor=self.admin,
        )

        self.assertEqual(
            created_count,
            0,
        )

        self.assertFalse(
            Notification.objects.exists()
        )

    def test_create_notifications_rejects_unknown_type(
        self,
    ):
        with self.assertRaises(ValueError):
            create_notifications(
                recipients=User.objects.all(),
                title="Invalid event",
                message="Invalid notification type.",
                notification_type="UNKNOWN",
            )

    def test_completed_operation_notifies_relevant_users(
        self,
    ):
        operation = SimpleNamespace(
            status="COMPLETED",
            assigned_staff_id=(
                self.ground_staff.id
            ),
            operation_type=(
                SimpleNamespace(
                    name="Baggage Handling",
                )
            ),
            flight=(
                SimpleNamespace(
                    flight_number="IR700",
                )
            ),
        )

        created_count = (
            notify_ground_operation_completed(
                operation=operation,
                actor=self.ground_staff,
            )
        )

        self.assertEqual(
            created_count,
            2,
        )

        self.assertEqual(
            self.recipient_ids(),
            {
                self.admin.id,
                self.manager.id,
            },
        )

        notification = (
            Notification.objects
            .filter(user=self.admin)
            .get()
        )

        self.assertEqual(
            notification.notification_type,
            "SUCCESS",
        )

        self.assertIn(
            "IR700",
            notification.message,
        )

    def test_incomplete_operation_creates_no_notification(
        self,
    ):
        operation = SimpleNamespace(
            status="IN_PROGRESS",
        )

        created_count = (
            notify_ground_operation_completed(
                operation=operation,
                actor=self.admin,
            )
        )

        self.assertEqual(
            created_count,
            0,
        )

        self.assertFalse(
            Notification.objects.exists()
        )

    def test_critical_security_report_notifies_security_roles(
        self,
    ):
        report = SimpleNamespace(
            severity="CRITICAL",
            reference="SEC-TEST-001",
            flight_id=None,
            flight=None,
            location="Terminal 1",
        )

        created_count = (
            notify_critical_security_report(
                report=report,
                actor=self.admin,
            )
        )

        self.assertEqual(
            created_count,
            2,
        )

        self.assertEqual(
            self.recipient_ids(),
            {
                self.manager.id,
                self.security_officer.id,
            },
        )

        notification = (
            Notification.objects
            .filter(
                user=self.security_officer,
            )
            .get()
        )

        self.assertEqual(
            notification.notification_type,
            "ERROR",
        )

        self.assertIn(
            "SEC-TEST-001",
            notification.message,
        )

    def test_noncritical_security_report_creates_no_notification(
        self,
    ):
        report = SimpleNamespace(
            severity="MEDIUM",
        )

        created_count = (
            notify_critical_security_report(
                report=report,
                actor=self.admin,
            )
        )

        self.assertEqual(
            created_count,
            0,
        )

        self.assertFalse(
            Notification.objects.exists()
        )

    def test_urgent_passenger_request_notifies_service_roles(
        self,
    ):
        passenger_request = SimpleNamespace(
            priority="URGENT",
            reference="PSR-TEST-001",
            passenger_name="Test Passenger",
            flight=(
                SimpleNamespace(
                    flight_number="W5100",
                )
            ),
            get_request_type_display=(
                lambda: "Wheelchair Assistance"
            ),
        )

        created_count = (
            notify_urgent_passenger_request(
                passenger_request=(
                    passenger_request
                ),
                actor=self.passenger_staff,
            )
        )

        self.assertEqual(
            created_count,
            2,
        )

        self.assertEqual(
            self.recipient_ids(),
            {
                self.admin.id,
                self.manager.id,
            },
        )

        notification = (
            Notification.objects
            .filter(user=self.admin)
            .get()
        )

        self.assertEqual(
            notification.notification_type,
            "WARNING",
        )

        self.assertIn(
            "PSR-TEST-001",
            notification.message,
        )

    def test_nonurgent_passenger_request_creates_no_notification(
        self,
    ):
        passenger_request = SimpleNamespace(
            priority="HIGH",
        )

        created_count = (
            notify_urgent_passenger_request(
                passenger_request=(
                    passenger_request
                ),
                actor=self.admin,
            )
        )

        self.assertEqual(
            created_count,
            0,
        )

        self.assertFalse(
            Notification.objects.exists()
        )