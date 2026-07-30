from functools import wraps

from django.core.exceptions import PermissionDenied


ADMIN = "ADMIN"
AIRPORT_MANAGER = "AIRPORT_MANAGER"
AIRLINE_OPERATOR = "AIRLINE_OPERATOR"
GROUND_STAFF = "GROUND_STAFF"
SECURITY_OFFICER = "SECURITY_OFFICER"
PASSENGER_SERVICE = "PASSENGER_SERVICE"


def has_role(user, roles):
    if not getattr(user, "is_authenticated", False):
        return False

    if user.is_superuser:
        return True

    return user.role in roles


def role_required(*roles):
    def decorator(view_function):
        @wraps(view_function)
        def wrapped_view(request, *args, **kwargs):
            if not has_role(request.user, roles):
                raise PermissionDenied

            return view_function(request, *args, **kwargs)

        return wrapped_view

    return decorator