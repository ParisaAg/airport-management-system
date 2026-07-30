from django.test import TestCase

# Create your tests here.
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .permissions import ADMIN, has_role


User = get_user_model()


class AuthenticationSecurityTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="ground-user",
            password="test-password",
            role="GROUND_STAFF",
        )

    def test_profile_requires_authentication(self):
        response = self.client.get(reverse("profile"))

        expected_url = (
            f"{reverse('login')}?next={reverse('profile')}"
        )

        self.assertRedirects(response, expected_url)

    def test_authenticated_user_is_redirected_from_login(self):
        self.client.force_login(self.user)

        response = self.client.get(reverse("login"))

        self.assertRedirects(response, reverse("dashboard"))

    def test_logout_rejects_get_request(self):
        self.client.force_login(self.user)

        response = self.client.get(reverse("logout"))

        self.assertEqual(response.status_code, 405)

    def test_logout_accepts_post_and_ends_session(self):
        self.client.force_login(self.user)

        response = self.client.post(reverse("logout"))

        self.assertRedirects(response, reverse("landing"))
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_superuser_is_accepted_for_admin_role(self):
        superuser = User.objects.create_superuser(
            username="root-admin",
            password="test-password",
            email="admin@example.com",
        )

        self.assertTrue(has_role(superuser, [ADMIN]))