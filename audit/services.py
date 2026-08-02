from .models import AuditLog


def get_request_ip(request):
    if request is None:
        return None

    return request.META.get(
        "REMOTE_ADDR"
    )


def record_audit_event(
    *,
    action,
    instance,
    description,
    actor=None,
    changes=None,
    request=None,
):
    authenticated_actor = None

    if (
        actor is not None
        and getattr(
            actor,
            "is_authenticated",
            False,
        )
    ):
        authenticated_actor = actor

    return AuditLog.objects.create(
        actor=authenticated_actor,
        action=action,
        entity_type=(
            instance._meta.label
        ),
        entity_id=str(
            instance.pk or ""
        ),
        description=description,
        changes=changes or {},
        ip_address=get_request_ip(
            request
        ),
    )