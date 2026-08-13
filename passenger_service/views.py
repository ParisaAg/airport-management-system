from django.contrib import messages
from django.contrib.auth.decorators import (
    login_required,
)
from django.core.exceptions import (
    PermissionDenied,
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
    role_required,
)
from notifications.services import (
    notify_urgent_passenger_request,
)
from audit.models import AuditLog
from audit.services import record_audit_event

from .forms import (
    PassengerAssignmentForm,
    PassengerRequestForm,
    PassengerResolutionForm,
)
from .models import PassengerRequest
from .selectors import (
    filter_passenger_requests,
    passenger_requests_visible_to,
    passenger_statistics,
)
from .services import (
    InvalidPassengerAssignment,
    InvalidPassengerTransition,
    assign_passenger_request,
    available_passenger_status_choices,
    transition_passenger_request_status,
)


AIRPORT_MANAGER = "AIRPORT_MANAGER"
PASSENGER_SERVICE = "PASSENGER_SERVICE"


PASSENGER_VIEW_ROLES = (
    ADMIN,
    AIRPORT_MANAGER,
    PASSENGER_SERVICE,
)


PASSENGER_MANAGE_ROLES = (
    ADMIN,
    PASSENGER_SERVICE,
)


@login_required
@role_required(*PASSENGER_VIEW_ROLES)
def passenger_request_list(request):
    base_queryset = (
        passenger_requests_visible_to(
            request.user
        )
    )

    statistics = passenger_statistics(
        base_queryset
    )

    search = request.GET.get(
        "search",
        "",
    ).strip()

    status = request.GET.get(
        "status",
        "",
    ).strip()

    priority = request.GET.get(
        "priority",
        "",
    ).strip()

    request_type = request.GET.get(
        "type",
        "",
    ).strip()

    assignment = request.GET.get(
        "assignment",
        "",
    ).strip()

    requests = filter_passenger_requests(
        base_queryset,
        search=search,
        status=status,
        priority=priority,
        request_type=request_type,
        assignment=assignment,
        user=request.user,
    )

    paginator = Paginator(
        requests,
        20,
    )

    page_obj = paginator.get_page(
        request.GET.get("page")
    )

    can_manage = (
        request.user.is_superuser
        or request.user.role
        in PASSENGER_MANAGE_ROLES
    )

    return render(
        request,
        "passenger_service/list.html",
        {
            "requests": (
                page_obj.object_list
            ),
            "page_obj": page_obj,
            "statistics": statistics,
            "statuses": (
                PassengerRequest
                .STATUS_CHOICES
            ),
            "priorities": (
                PassengerRequest
                .PRIORITY_CHOICES
            ),
            "request_types": (
                PassengerRequest
                .REQUEST_TYPE_CHOICES
            ),
            "selected_search": search,
            "selected_status": status,
            "selected_priority": priority,
            "selected_type": request_type,
            "selected_assignment": (
                assignment
            ),
            "can_manage": can_manage,
        },
    )


@login_required
@role_required(*PASSENGER_VIEW_ROLES)
def passenger_request_detail(
    request,
    id,
):
    passenger_request = (
        get_object_or_404(
            passenger_requests_visible_to(
                request.user
            ),
            id=id,
        )
    )

    can_manage = (
        request.user.is_superuser
        or request.user.role
        in PASSENGER_MANAGE_ROLES
    )

    can_change_status = (
        request.user.is_superuser
        or request.user.role == ADMIN
        or (
            request.user.role
            == PASSENGER_SERVICE
            and (
                passenger_request
                .assigned_staff_id
                == request.user.id
            )
        )
    )

    allowed_statuses = (
        available_passenger_status_choices(
            passenger_request.status
        )
    )

    if passenger_request.status == "OPEN":
        allowed_statuses = [
            choice
            for choice in allowed_statuses
            if choice[0] != "ASSIGNED"
        ]

    assignment_form = (
        PassengerAssignmentForm(
            initial={
                "staff": (
                    passenger_request
                    .assigned_staff_id
                ),
            }
        )
    )

    resolution_form = (
        PassengerResolutionForm()
    )

    return render(
        request,
        "passenger_service/detail.html",
        {
            "passenger_request": (
                passenger_request
            ),
            "allowed_statuses": (
                allowed_statuses
            ),
            "assignment_form": (
                assignment_form
            ),
            "resolution_form": (
                resolution_form
            ),
            "can_manage": can_manage,
            "can_change_status": (
                can_change_status
            ),
        },
    )


@login_required
@role_required(
    *PASSENGER_MANAGE_ROLES
)
def passenger_request_create(
    request,
):
    if request.method == "POST":
        form = PassengerRequestForm(
            request.POST
        )

        if form.is_valid():
            passenger_request = (
                form.save()
            )

            record_audit_event(
                action=(
                    AuditLog.Action.CREATE
                ),
                instance=passenger_request,
                actor=request.user,
                request=request,
                description=(
                    f"{passenger_request.reference} "
                    "passenger service request "
                    "created."
                ),
                changes={
                    "status": {
                        "from": None,
                        "to": "OPEN",
                    },
                    "priority": {
                        "from": None,
                        "to": (
                            passenger_request
                            .priority
                        ),
                    },
                },
            )

            notify_urgent_passenger_request(
                passenger_request=(
                    passenger_request
                ),
                actor=request.user,
            )

            messages.success(
                request,
                (
                    f"{passenger_request.reference} "
                    "created successfully."
                ),
            )

            return redirect(
                "passenger_service:detail",
                id=passenger_request.id,
            )
    else:
        form = PassengerRequestForm()

    return render(
        request,
        "passenger_service/form.html",
        {
            "form": form,
            "edit": False,
        },
    )

@login_required
@require_POST
@role_required(*PASSENGER_MANAGE_ROLES)
def passenger_request_assign(
    request,
    id,
):
    passenger_request = (
        get_object_or_404(
            PassengerRequest,
            id=id,
        )
    )

    form = PassengerAssignmentForm(
        request.POST
    )

    if form.is_valid():
        staff = form.cleaned_data[
            "staff"
        ]

        try:
            passenger_request = (
                assign_passenger_request(
                    request_id=(
                        passenger_request.id
                    ),
                    staff=staff,
                    actor=request.user,
                    request=request,
                )
            )

        except InvalidPassengerAssignment as error:
            messages.error(
                request,
                error.messages[0],
            )

        else:
            messages.success(
                request,
                (
                    f"{passenger_request.reference} "
                    f"assigned to "
                    f"{staff.username}."
                ),
            )

    else:
        messages.error(
            request,
            (
                "Select a valid passenger "
                "service staff member."
            ),
        )

    return redirect(
        "passenger_service:detail",
        id=passenger_request.id,
    )


@login_required
@require_POST
@role_required(*PASSENGER_MANAGE_ROLES)
def passenger_request_change_status(
    request,
    id,
):
    passenger_request = (
        get_object_or_404(
            PassengerRequest,
            id=id,
        )
    )

    is_admin = (
        request.user.is_superuser
        or request.user.role == ADMIN
    )

    is_assigned_agent = (
        request.user.role
        == PASSENGER_SERVICE
        and (
            passenger_request
            .assigned_staff_id
            == request.user.id
        )
    )

    if not (
        is_admin
        or is_assigned_agent
    ):
        raise PermissionDenied

    new_status = request.POST.get(
        "status",
        "",
    ).strip()

    resolution_notes = (
        request.POST.get(
            "resolution_notes",
            "",
        ).strip()
    )

    try:
        passenger_request = (
            transition_passenger_request_status(
                request_id=(
                    passenger_request.id
                ),
                new_status=new_status,
                actor=request.user,
                request=request,
                resolution_notes=(
                    resolution_notes
                ),
            )
        )

    except InvalidPassengerTransition as error:
        messages.error(
            request,
            error.messages[0],
        )

    else:
        messages.success(
            request,
            (
                f"{passenger_request.reference} "
                f"changed to "
                f"{passenger_request.get_status_display()}."
            ),
        )

    return redirect(
        "passenger_service:detail",
        id=passenger_request.id,
    )