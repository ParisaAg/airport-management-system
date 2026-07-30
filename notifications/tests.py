from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .models import Notification


User = get_user_model()


class NotificationPrivacyTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="notification-owner",
            password="test-password",
            role="ADMIN",
        )

        self.other_user = User.objects.create_user(
            username="another-user",
            password="test-password",
            role="ADMIN",
        )

        self.own_notification = Notification.objects.create(
            user=self.user,
            title="Private notification",
            message="Visible to the owner only.",
        )

        self.other_notification = Notification.objects.create(
            user=self.other_user,
            title="Another user's notification",
            message="This notification must not be exposed.",
        )

    def test_notification_list_requires_authentication(self):
        response = self.client.get(
            reverse("notifications")
        )

        expected_url = (
            f"{reverse('login')}"
            f"?next={reverse('notifications')}"
        )

        self.assertRedirects(response, expected_url)

    def test_user_only_sees_own_notifications(self):
        self.client.force_login(self.user)

        response = self.client.get(
            reverse("notifications")
        )

        self.assertContains(
            response,
            self.own_notification.title,
        )

        self.assertNotContains(
            response,
            self.other_notification.title,
        )

    def test_mark_as_read_rejects_get_request(self):
        self.client.force_login(self.user)

        response = self.client.get(
            reverse(
                "mark_as_read",
                args=[self.own_notification.pk],
            )
        )

        self.assertEqual(response.status_code, 405)

    def test_user_cannot_modify_another_users_notification(self):
        self.client.force_login(self.user)

        response = self.client.post(
            reverse(
                "mark_as_read",
                args=[self.other_notification.pk],
            )
        )

        self.assertEqual(response.status_code, 404)

        self.other_notification.refresh_from_db()
        self.assertFalse(self.other_notification.is_read)

    def test_owner_can_mark_notification_as_read(self):
        self.client.force_login(self.user)

        response = self.client.post(
            reverse(
                "mark_as_read",
                args=[self.own_notification.pk],
            )
        )

        self.assertRedirects(
            response,
            reverse("notifications"),
        )

        self.own_notification.refresh_from_db()
        self.assertTrue(self.own_notification.is_read)