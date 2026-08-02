from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.test import RequestFactory, TestCase

from .admin import AuditLogAdmin
from .models import AuditLog
from .services import record_audit_event


User = get_user_model()


class AuditServiceTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="audit-admin",
            password="test-password",
            role="ADMIN",
        )

        self.request = RequestFactory().post(
            "/flights/1/status/",
            REMOTE_ADDR="127.0.0.1",
        )

        self.request.user = self.user

    def test_audit_event_records_actor_and_changes(self):
        event = record_audit_event(
            action=AuditLog.Action.STATUS_CHANGE,
            instance=self.user,
            description="User status changed.",
            actor=self.user,
            request=self.request,
            changes={
                "status": {
                    "from": "SCHEDULED",
                    "to": "DELAYED",
                }
            },
        )

        self.assertEqual(
            event.actor,
            self.user,
        )

        self.assertEqual(
            event.entity_type,
            "accounts.User",
        )

        self.assertEqual(
            event.entity_id,
            str(self.user.id),
        )

        self.assertEqual(
            event.ip_address,
            "127.0.0.1",
        )

        self.assertEqual(
            event.changes["status"]["to"],
            "DELAYED",
        )

    def test_anonymous_actor_is_stored_as_system(self):
        event = record_audit_event(
            action=AuditLog.Action.LOGIN,
            instance=self.user,
            description="Anonymous event.",
            actor=AnonymousUser(),
        )

        self.assertIsNone(
            event.actor,
        )


class AuditAdminTests(TestCase):
    def setUp(self):
        self.admin_user = User.objects.create_superuser(
            username="root-admin",
            password="test-password",
            email="root@example.com",
        )

        self.request = RequestFactory().get(
            "/admin/audit/auditlog/"
        )

        self.request.user = self.admin_user

        self.model_admin = AuditLogAdmin(
            AuditLog,
            admin.site,
        )

    def test_audit_records_are_immutable_in_admin(self):
        self.assertFalse(
            self.model_admin.has_add_permission(
                self.request
            )
        )

        self.assertFalse(
            self.model_admin.has_change_permission(
                self.request
            )
        )

        self.assertFalse(
            self.model_admin.has_delete_permission(
                self.request
            )
        )