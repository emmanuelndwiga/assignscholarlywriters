import json

from django.conf import settings
from django.contrib import messages
from django.http import JsonResponse, HttpResponseForbidden
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_http_methods
from django_ratelimit.decorators import ratelimit

from cases.models import CaseReport, Attachment, generate_tracking_code
from notifications.models import PushSubscription
from .forms import CaseReportForm, TrackingForm, ReplyForm, ALLOWED_ATTACHMENT_TYPES, MAX_ATTACHMENT_SIZE


def landing(request):
    return render(request, "public/landing.html")


@ratelimit(key="ip", rate="10/h", method="POST", block=True)
def submit_report(request):
    if request.method == "POST":
        form = CaseReportForm(request.POST)
        if form.is_valid():
            case = form.save(commit=False)
            raw_code = generate_tracking_code()
            case.set_tracking_code(raw_code)
            case.save()

            for f in request.FILES.getlist("attachments"):
                if f.content_type in ALLOWED_ATTACHMENT_TYPES and f.size <= MAX_ATTACHMENT_SIZE:
                    Attachment.objects.create(
                        case=case, file=f, original_filename=f.name,
                        content_type=f.content_type, size=f.size,
                    )

            return render(request, "public/submitted.html", {
                "reference_number": case.reference_number,
                "tracking_code": raw_code,
            })
    else:
        form = CaseReportForm()
    return render(request, "public/submit.html", {"form": form})


@ratelimit(key="ip", rate="20/h", method="POST", block=True)
def track_case(request):
    result = None
    error = None
    tracking_code = None
    if request.method == "POST":
        form = TrackingForm(request.POST)
        if form.is_valid():
            case = CaseReport.objects.filter(
                reference_number=form.cleaned_data["reference_number"]
            ).first()
            if case and case.check_tracking_code(form.cleaned_data["tracking_code"]):
                result = case
                tracking_code = form.cleaned_data["tracking_code"]
                case.updates.filter(visibility="victim").update(is_read_by_victim=True)
            else:
                error = "Invalid reference number or tracking code."
    else:
        form = TrackingForm()

    if result:
        return render(request, "public/status.html", {
            "case": result,
            "tracking_code": tracking_code,
            "vapid_public_key": settings.VAPID_PUBLIC_KEY,
        })
    return render(request, "public/track.html", {"form": form, "error": error})


@ratelimit(key="ip", rate="30/h", method="POST", block=True)
def reply_to_case(request, pk):
    ref = request.POST.get("reference_number")
    code = request.POST.get("tracking_code")
    message = request.POST.get("message", "").strip()

    case = CaseReport.objects.filter(pk=pk, reference_number=ref).first()
    if not case or not case.check_tracking_code(code) or not message:
        messages.error(request, "We couldn't verify your details. Please try tracking your report again.")
        return redirect("public:track")

    from cases.models import CaseUpdate
    from notifications import services as notification_services
    update = CaseUpdate.objects.create(case=case, author_type="victim", message=message, visibility="victim")
    messages.success(request, "Your message has been sent.")
    notification_services.notify_staff(case, update=update)

    return render(request, "public/status.html", {
        "case": case,
        "tracking_code": code,
        "vapid_public_key": settings.VAPID_PUBLIC_KEY,
    })


@ratelimit(key="ip", rate="20/h", method="POST", block=True)
def push_subscribe(request):
    data = json.loads(request.body)
    case = CaseReport.objects.filter(reference_number=data.get("reference_number")).first()
    if not case or not case.check_tracking_code(data.get("tracking_code", "")):
        return JsonResponse({"error": "invalid credentials"}, status=403)

    sub = data["subscription"]
    PushSubscription.objects.update_or_create(
        endpoint=sub["endpoint"],
        defaults={
            "case": case, "user": None,
            "p256dh_key": sub["keys"]["p256dh"],
            "auth_key": sub["keys"]["auth"],
        },
    )
    return JsonResponse({"status": "subscribed"})


def service_worker(request):
    return render(request, "public/sw.js", content_type="application/javascript")


def ratelimited_view(request, exception):
    return HttpResponseForbidden("Too many requests. Please try again shortly.")