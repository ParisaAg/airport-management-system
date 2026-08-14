from unittest.mock import patch

from django.db.utils import DatabaseError
from django.test import TestCase
from django.urls import reverse


class HealthCheckTests(TestCase):
    def test_health_check_is_public_and_healthy(
        self,
    ):
        response = self.client.get(
            reverse("health_check")
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertEqual(
            response.json(),
            {
                "status": "healthy",
                "database": "available",
            },
        )

    @patch(
        "config.views.connection.cursor"
    )
    def test_health_check_reports_database_failure(
        self,
        cursor_mock,
    ):
        cursor_mock.side_effect = (
            DatabaseError(
                "Database unavailable"
            )
        )

        response = self.client.get(
            reverse("health_check")
        )

        self.assertEqual(
            response.status_code,
            503,
        )

        self.assertEqual(
            response.json(),
            {
                "status": "unhealthy",
                "database": "unavailable",
            },
        )