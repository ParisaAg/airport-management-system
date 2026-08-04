from django.conf import settings
from django.db import models


class AuditLog(models.Model):
    class Action(models.TextChoices):
        CREATE = "CREATE", "Create"
        UPDATE = "UPDATE", "Update"
        DELETE = "DELETE", "Delete"
        STATUS_CHANGE = "STATUS_CHANGE", "Status Change"
        ASSIGN = "ASSIGN", "Assign"
        RELEASE = "RELEASE", "Release"
        LOGIN = "LOGIN", "Login"
        LOGOUT = "LOGOUT", "Logout"

    class EntityType(models.TextChoices):
        FLIGHT = "FLIGHT", "Flight"
        GROUND_OPERATION = (
            "GROUND_OPERATION",
            "Ground Operation",
        )
        GATE_ASSIGNMENT = (
            "GATE_ASSIGNMENT",
            "Gate Assignment",
        )

    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="audit_events",
    )

    action = models.CharField(
        max_length=30,
        choices=Action.choices,
        db_index=True,
    )

    entity_type = models.CharField(
        max_length=100,
        choices=EntityType.choices,
        db_index=True,
    )

    entity_id = models.CharField(
        max_length=100,
        blank=True,
    )

    description = models.CharField(
        max_length=255,
    )

    changes = models.JSONField(
        default=dict,
        blank=True,
    )

    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        db_index=True,
    )

    class Meta:
        ordering = ["-created_at"]

        indexes = [
            models.Index(
                fields=["entity_type", "entity_id"],
                name="audit_entity_lookup",
            ),
            models.Index(
                fields=["actor", "created_at"],
                name="audit_actor_time",
            ),
        ]

        verbose_name = "Audit Log"
        verbose_name_plural = "Audit Logs"

    def __str__(self):
        actor_name = (
            self.actor.username
            if self.actor
            else "System"
        )

        return (
            f"{actor_name} - "
            f"{self.action} - "
            f"{self.entity_type}"
        )