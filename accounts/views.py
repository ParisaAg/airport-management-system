from django.contrib import messages
from django.contrib.auth import (
    authenticate,
    login,
    logout,
)
from django.contrib.auth.decorators import (
    login_required,
)
from django.shortcuts import redirect, render
from django.views.decorators.http import (
    require_POST,
)

from .forms import RegistrationForm


def login_view(request):
    if request.user.is_authenticated:
        return redirect("dashboard")

    if request.method == "POST":
        username = request.POST.get(
            "username"
        )

        password = request.POST.get(
            "password"
        )

        user = authenticate(
            request,
            username=username,
            password=password,
        )

        if user is not None:
            login(
                request,
                user,
            )

            return redirect("dashboard")

        messages.error(
            request,
            "Invalid username or password",
        )

    return render(
        request,
        "accounts/login.html",
    )


def register_view(request):
    if request.user.is_authenticated:
        return redirect("dashboard")

    if request.method == "POST":
        form = RegistrationForm(
            request.POST
        )

        if form.is_valid():
            user = form.save()

            login(
                request,
                user,
            )

            messages.success(
                request,
                (
                    "Your account has been "
                    "created successfully."
                ),
            )

            return redirect("dashboard")
    else:
        form = RegistrationForm()

    return render(
        request,
        "accounts/register.html",
        {
            "form": form,
        },
    )


@login_required
@require_POST
def logout_view(request):
    list(
        messages.get_messages(request)
    )

    logout(request)

    return redirect("landing")


@login_required
def profile_view(request):
    return render(
        request,
        "accounts/profile.html",
        {
            "user": request.user,
        },
    )