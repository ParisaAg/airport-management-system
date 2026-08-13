from django.contrib import messages
from django.contrib.auth.decorators import (
    login_required,
)
from django.core.paginator import Paginator
from django.shortcuts import (
    get_object_or_404,
    redirect,
    render,
)
from django.views.decorators.http import (
    require_POST,
)

from accounts.permissions import (
    ADMIN,
    AIRPORT_MANAGER,
    SECURITY_OFFICER,
    role_required,
)
from audit.models import AuditLog
from audit.services import record_audit_event
from notifications.services import (
    notify_critical_security_report,
)
from .forms import (
    SecurityAssignmentForm,
    SecurityReportForm,
    SecurityResolutionForm,
)
from .models import SecurityReport
from .selectors import (
    filter_security_reports,
    security_reports_visible_to,
    security_statistics,
)
from .services import (
    InvalidSecurityAssignment,
    InvalidSecurityTransition,
    assign_security_officer,
    available_security_status_choices,
    transition_security_report_status,
)


SECURITY_VIEW_ROLES = (
    ADMIN,
    AIRPORT_MANAGER,
    SECURITY_OFFICER,
)

SECURITY_MANAGE_ROLES = (
    ADMIN,
    SECURITY_OFFICER,
)


@login_required
@role_required(*SECURITY_VIEW_ROLES)
def security_report_list(request):
    base_queryset = (
        security_reports_visible_to(
            request.user
        )
    )

    statistics = (
        security_statistics(
            base_queryset
        )
    )

    search = request.GET.get(
        "search",
        "",
    ).strip()

    status = request.GET.get(
        "status",
        "",
    ).strip()

    severity = request.GET.get(
        "severity",
        "",
    ).strip()

    report_type = request.GET.get(
        "type",
        "",
    ).strip()

    assignment = request.GET.get(
        "assignment",
        "",
    ).strip().upper()

    reports = filter_security_reports(
        base_queryset,
        search=search,
        status=status,
        severity=severity,
        report_type=report_type,
        assignment=assignment,
        user=request.user,
    )

    paginator = Paginator(
        reports,
        20,
    )

    page_obj = paginator.get_page(
        request.GET.get("page")
    )

    return render(
        request,
        "security/list.html",
        {
            "page_obj": page_obj,
            "reports": page_obj.object_list,
            "statistics": statistics,
            "statuses": (
                SecurityReport.STATUS_CHOICES
            ),
            "severities": (
                SecurityReport.SEVERITY_CHOICES
            ),
            "report_types": (
                SecurityReport
                .REPORT_TYPE_CHOICES
            ),
            "search": search,
            "selected_status": status,
            "selected_severity": severity,
            "selected_type": report_type,
            "selected_assignment": (
                assignment
            ),
            "can_manage_security": (
                request.user.is_superuser
                or request.user.role
                in SECURITY_MANAGE_ROLES
            ),
        },
    )


@login_required
@role_required(*SECURITY_VIEW_ROLES)
def security_report_detail(
    request,
    id,
):
    report = get_object_or_404(
        security_reports_visible_to(
            request.user
        ),
        id=id,
    )

    can_manage = (
        request.user.is_superuser
        or request.user.role
        in SECURITY_MANAGE_ROLES
    )

    assignment_form = (
        SecurityAssignmentForm(
            initial={
                "officer": (
                    report.officer_id
                )
            }
        )
    )

    resolution_form = (
        SecurityResolutionForm()
    )

    return render(
        request,
        "security/detail.html",
        {
            "report": report,
            "allowed_statuses": (
                available_security_status_choices(
                    report.status
                )
            ),
            "assignment_form": (
                assignment_form
            ),
            "resolution_form": (
                resolution_form
            ),
            "can_manage_security": (
                can_manage
            ),
        },
    )


@login_required
@role_required(
    *SECURITY_MANAGE_ROLES
)
def security_report_create(
    request,
):
    if request.method == "POST":
        form = SecurityReportForm(
            request.POST
        )

        if form.is_valid():
            report = form.save()

            record_audit_event(
                action=(
                    AuditLog.Action.CREATE
                ),
                instance=report,
                actor=request.user,
                request=request,
                description=(
                    f"{report.reference} "
                    "security incident created."
                ),
                changes={
                    "status": {
                        "from": None,
                        "to": report.status,
                    },
                    "severity": {
                        "from": None,
                        "to": report.severity,
                    },
                },
            )

            notify_critical_security_report(
                report=report,
                actor=request.user,
            )

            messages.success(
                request,
                (
                    f"{report.reference} "
                    "created successfully."
                ),
            )

            return redirect(
                "security:detail",
                id=report.id,
            )
    else:
        form = SecurityReportForm()

    return render(
        request,
        "security/form.html",
        {
            "form": form,
            "edit": False,
        },
    )


@login_required
@require_POST
@role_required(
    *SECURITY_MANAGE_ROLES
)
def security_report_assign(
    request,
    id,
):
    report = get_object_or_404(
        SecurityReport,
        id=id,
    )

    form = SecurityAssignmentForm(
        request.POST
    )

    if not form.is_valid():
        messages.error(
            request,
            (
                "Select a valid "
                "security officer."
            ),
        )

        return redirect(
            "security:detail",
            id=report.id,
        )

    try:
        assign_security_officer(
            report_id=report.id,
            officer=(
                form.cleaned_data[
                    "officer"
                ]
            ),
            actor=request.user,
            request=request,
        )

    except InvalidSecurityAssignment as error:
        messages.error(
            request,
            error.messages[0],
        )

    else:
        messages.success(
            request,
            (
                "Security officer "
                "assigned successfully."
            ),
        )

    return redirect(
        "security:detail",
        id=report.id,
    )


@login_required
@require_POST
@role_required(
    *SECURITY_MANAGE_ROLES
)
def security_report_change_status(
    request,
    id,
):
    report = get_object_or_404(
        SecurityReport,
        id=id,
    )

    new_status = request.POST.get(
        "status",
        "",
    ).strip()

    resolution_notes = (
        request.POST.get(
            "resolution_notes",
            "",
        )
    )

    try:
        transition_security_report_status(
            report_id=report.id,
            new_status=new_status,
            actor=request.user,
            request=request,
            resolution_notes=(
                resolution_notes
            ),
        )

    except InvalidSecurityTransition as error:
        messages.error(
            request,
            error.messages[0],
        )

    else:
        messages.success(
            request,
            (
                f"{report.reference} "
                "status updated."
            ),
        )

    return redirect(
        "security:detail",
        id=report.id,
    )