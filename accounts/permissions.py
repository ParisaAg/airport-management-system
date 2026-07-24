from django.contrib.auth.models import AnonymousUser


def has_role(user, roles):

    if not user.is_authenticated:
        return False

    if user.is_superuser:
        return True

    return user.role in roles




def has_role(user, roles):

    if isinstance(user, AnonymousUser):
        return False

    return user.role in roles