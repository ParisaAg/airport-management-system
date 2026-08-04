from django.db.models import Q

from .models import AuditLog


def filtered_audit_logs(
    *,
    search="",
    action="",
    entity_type="",
):
    logs = AuditLog.objects.select_related(
        "actor",
    ).all()

    if search:
        logs = logs.filter(
            Q(description__icontains=search)
            | Q(actor__username__icontains=search)
            | Q(entity_id__icontains=search)
        )

    valid_actions = {
        value
        for value, _label in AuditLog.Action.choices
    }

    if action in valid_actions:
        logs = logs.filter(
            action=action,
        )

    valid_entity_types = {
        value
        for value, _label
        in AuditLog.EntityType.choices
    }

    if entity_type in valid_entity_types:
        logs = logs.filter(
            entity_type=entity_type,
        )

    return logs