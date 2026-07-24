from .models import User


def user_role(request):

    role = None

    if request.user.is_authenticated:

        role = request.user.role


    return {
        "role": role
    }