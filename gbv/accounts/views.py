# accounts/views.py
from django.contrib.auth import authenticate, login, logout, get_user_model
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django_ratelimit.decorators import ratelimit

from .decorators import role_required
from .forms import StaffLoginForm, InviteHandlerForm, AcceptInvitationForm
from .models import StaffInvitation

User = get_user_model()


@ratelimit(key="ip", rate="10/h", method="POST", block=True)
def staff_login(request):
    if request.user.is_authenticated:
        return redirect("cases:dashboard")

    if request.method == "POST":
        form = StaffLoginForm(request.POST)
        if form.is_valid():
            user = authenticate(
                request,
                username=form.cleaned_data["username"],
                password=form.cleaned_data["password"],
            )
            if user is not None:
                login(request, user)
                next_url = request.GET.get("next")
                return redirect(next_url or "cases:dashboard")
            form.add_error(None, "Invalid credentials")
    else:
        form = StaffLoginForm()

    return render(request, "accounts/login.html", {"form": form})


def staff_logout(request):
    logout(request)
    messages.info(request, "You have been logged out.")
    return redirect("accounts:login")


@role_required("supervisor")
def invite_handler(request):
    if request.method == "POST":
        form = InviteHandlerForm(request.POST)
        if form.is_valid():
            invitation = form.save(commit=False)
            invitation.invited_by = request.user
            invitation.save()

            link = request.build_absolute_uri(
                f"/staff/invite/{invitation.token}/"
            )
            send_mail(
                subject="You've been invited to the GBV reporting platform",
                message=(
                    f"You've been invited as a {invitation.get_role_display()}.\n"
                    f"Set up your account here: {link}\n"
                    f"This link expires on {invitation.expires_at:%Y-%m-%d %H:%M}."
                ),
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[invitation.email],
                fail_silently=False,
            )
            messages.success(request, f"Invitation sent to {invitation.email}.")
            return redirect("accounts:create_handler")
    else:
        form = InviteHandlerForm()

    pending = StaffInvitation.objects.filter(accepted_at__isnull=True).order_by("-created_at")
    return render(request, "accounts/invite_handler.html", {"form": form, "pending": pending})


@ratelimit(key="ip", rate="10/h", method="POST", block=True)
def accept_invitation(request, token):
    invitation = get_object_or_404(StaffInvitation, token=token)

    if not invitation.is_valid():
        return render(request, "accounts/invite_invalid.html", status=410)

    if request.method == "POST":
        form = AcceptInvitationForm(request.POST)
        if form.is_valid():
            user = User.objects.create_user(
                username=form.cleaned_data["username"],
                email=invitation.email,
                password=form.cleaned_data["password"],
                role=invitation.role,
            )
            invitation.accepted_at = timezone.now()
            invitation.save(update_fields=["accepted_at"])

            login(request, user)
            messages.success(request, "Account created. Welcome aboard.")
            return redirect("cases:dashboard")
    else:
        form = AcceptInvitationForm()

    return render(
        request, "accounts/accept_invitation.html", {"form": form, "invitation": invitation}
    )