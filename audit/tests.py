from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.test import RequestFactory, TestCase
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from .models import AuditLog
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

class AuditLogListViewTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        user_model = get_user_model()

        cls.admin = user_model.objects.create_user(
            username="audit-admin",
            password="test-password",
            role="ADMIN",
        )

        cls.ground_staff = user_model.objects.create_user(
            username="audit-ground-staff",
            password="test-password",
            role="GROUND_STAFF",
        )

        cls.flight_event = AuditLog.objects.create(
            actor=cls.admin,
            action=AuditLog.Action.STATUS_CHANGE,
            entity_type=AuditLog.EntityType.FLIGHT,
            entity_id="101",
            description="Flight IR101 changed to boarding.",
        )

        cls.gate_event = AuditLog.objects.create(
            actor=cls.admin,
            action=AuditLog.Action.ASSIGN,
            entity_type=(
                AuditLog.EntityType.GATE_ASSIGNMENT
            ),
            entity_id="202",
            description="Gate A12 assigned to flight IR101.",
        )

    def test_anonymous_user_is_redirected_to_login(self):
        response = self.client.get(
            reverse("audit:list"),
        )

        self.assertEqual(
            response.status_code,
            302,
        )

        self.assertIn(
            reverse("login"),
            response.url,
        )

    def test_non_admin_user_cannot_access_audit_center(self):
        self.client.force_login(
            self.ground_staff,
        )

        response = self.client.get(
            reverse("audit:list"),
        )

        self.assertEqual(
            response.status_code,
            403,
        )

    def test_admin_can_access_audit_center(self):
        self.client.force_login(
            self.admin,
        )

        response = self.client.get(
            reverse("audit:list"),
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertTemplateUsed(
            response,
            "audit/list.html",
        )

        self.assertContains(
            response,
            self.flight_event.description,
        )

        self.assertContains(
            response,
            self.gate_event.description,
        )

    def test_action_filter_only_returns_matching_events(self):
        self.client.force_login(
            self.admin,
        )

        response = self.client.get(
            reverse("audit:list"),
            {
                "action": AuditLog.Action.ASSIGN,
            },
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertContains(
            response,
            self.gate_event.description,
        )

        self.assertNotContains(
            response,
            self.flight_event.description,
        )

    def test_entity_filter_only_returns_matching_events(self):
        self.client.force_login(
            self.admin,
        )

        response = self.client.get(
            reverse("audit:list"),
            {
                "entity_type": (
                    AuditLog.EntityType.FLIGHT
                ),
            },
        )

        self.assertContains(
            response,
            self.flight_event.description,
        )

        self.assertNotContains(
            response,
            self.gate_event.description,
        )

    def test_search_matches_event_description(self):
        self.client.force_login(
            self.admin,
        )

        response = self.client.get(
            reverse("audit:list"),
            {
                "search": "A12",
            },
        )

        self.assertContains(
            response,
            self.gate_event.description,
        )

        self.assertNotContains(
            response,
            self.flight_event.description,
        )

    def test_audit_logs_are_paginated(self):
        for number in range(21):
            AuditLog.objects.create(
                actor=self.admin,
                action=AuditLog.Action.UPDATE,
                entity_type=AuditLog.EntityType.FLIGHT,
                entity_id=str(number),
                description=(
                    f"Pagination audit event {number}."
                ),
            )

        self.client.force_login(
            self.admin,
        )

        response = self.client.get(
            reverse("audit:list"),
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        page = response.context["page"]

        self.assertEqual(
            page.paginator.per_page,
            20,
        )

        self.assertEqual(
            page.paginator.num_pages,
            2,
        )

        self.assertEqual(
            len(response.context["logs"]),
            20,
        )