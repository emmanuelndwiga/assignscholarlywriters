import secrets
from django.shortcuts import render
from django.views.decorators.http import require_http_methods
from cases.models import CaseReport
from .forms import CaseReportForm, TrackingForm
from django_ratelimit.decorators import ratelimit
# public/views.py
from django.http import HttpResponseForbidden

def ratelimited_view(request, exception):
    return HttpResponseForbidden("Too many requests. Please try again later.")

def submit_report(request):
    if request.method == "POST":
        form = CaseReportForm(request.POST)
        if form.is_valid():
            case = form.save(commit=False)
            raw_code = secrets.token_urlsafe(6)
            case.set_tracking_code(raw_code)
            case.save()

            for f in request.FILES.getlist("attachments"):
                if f.content_type in ALLOWED_TYPES and f.size <= MAX_SIZE:
                    Attachment.objects.create(
                        case=case, file=f, original_filename=f.name,
                        content_type=f.content_type, size=f.size,
                    )

            return render(request, "public/submitted.html", {
                "reference_number": case.reference_number,
                "tracking_code": raw_code,
            })

@require_http_methods(["GET", "POST"])
def track_case(request):
    result = None
    error = None
    if request.method == "POST":
        form = TrackingForm(request.POST)
        if form.is_valid():
            case = CaseReport.objects.filter(
                reference_number=form.cleaned_data["reference_number"]
            ).first()
            if case and case.check_tracking_code(form.cleaned_data["tracking_code"]):
                result = case
            else:
                error = "Invalid reference number or tracking code."
    else:
        form = TrackingForm()
    return render(request, "public/track.html", {"form": form, "case": result, "error": error})