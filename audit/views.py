from django.core.paginator import Paginator
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from accounts.permissions import ADMIN, role_required
from .models import AuditLog
from .selectors import filtered_audit_logs

@login_required
@role_required(ADMIN)
def audit_log_list(request):
    search = request.GET.get(
        "search",
        "",
    ).strip()

    action = request.GET.get(
        "action",
        "",
    ).strip()

    entity_type = request.GET.get(
        "entity_type",
        "",
    ).strip()

    logs = filtered_audit_logs(
        search=search,
        action=action,
        entity_type=entity_type,
    )

    paginator = Paginator(
        logs,
        20,
    )

    page = paginator.get_page(
        request.GET.get("page"),
    )

    return render(
        request,
        "audit/list.html",
        {
            "page": page,
            "logs": page.object_list,
            "actions": AuditLog.Action.choices,
            "entity_types": (
                AuditLog.EntityType.choices
            ),
            "selected_action": action,
            "selected_entity_type": entity_type,
            "search": search,
        },
    )