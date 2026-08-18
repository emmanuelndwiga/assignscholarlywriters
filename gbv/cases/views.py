from django.db.models import Q
from django.shortcuts import render, get_object_or_404, redirect
from accounts.decorators import role_required
from notifications import services as notification_services
from .models import CaseReport, CaseAuditLog, CaseUpdate

def _get_case_for_staff(request, pk):
    """Fetch a case and enforce that handlers only reach their own/unassigned cases."""
    case = get_object_or_404(CaseReport, pk=pk)
    if request.user.role == "case_handler" and case.assigned_handler_id not in (None, request.user.id):
        from django.core.exceptions import PermissionDenied
        raise PermissionDenied
    return case

@role_required("case_handler", "supervisor")
def dashboard(request):
    if request.user.role == "supervisor":
        cases = CaseReport.objects.all().order_by("-created_at")
    else:
        cases = CaseReport.objects.filter(
            Q(assigned_handler=request.user) | Q(assigned_handler__isnull=True)
        ).order_by("-created_at")
    return render(request, "cases/dashboard.html", {"cases": cases})

@role_required("case_handler", "supervisor")
def case_detail(request, pk):
    case = _get_case_for_staff(request, pk)
    return render(request, "cases/detail.html", {"case": case})

@role_required("case_handler", "supervisor")
def update_status(request, pk):
    case = _get_case_for_staff(request, pk)
    if request.method == "POST":
        new_status = request.POST.get("status")
        case.status = new_status
        case.save(update_fields=["status", "updated_at"])
        CaseAuditLog.objects.create(case=case, actor=request.user, action="status_changed", detail=new_status)
        notification_services.notify_victim(case)
    return redirect("cases:detail", pk=pk)

@role_required("case_handler", "supervisor")
def add_update(request, pk):
    case = _get_case_for_staff(request, pk)
    if request.method == "POST":
        message = request.POST.get("message", "").strip()
        if message:
            update = CaseUpdate.objects.create(
                case=case,
                author_type=CaseUpdate.AuthorType.HANDLER,
                author_user=request.user,
                message=message,
                visibility=request.POST.get("visibility", CaseUpdate.Visibility.VICTIM),
            )
            CaseAuditLog.objects.create(case=case, actor=request.user, action="update_added")
            if update.visibility == CaseUpdate.Visibility.VICTIM:
                notification_services.notify_victim(case, update=update)
    return redirect("cases:detail", pk=pk)

@role_required("supervisor")
def escalate(request, pk):
    case = get_object_or_404(CaseReport, pk=pk)
    if request.method == "POST":
        case.status = CaseReport.Status.ESCALATED
        case.save(update_fields=["status", "updated_at"])
        CaseAuditLog.objects.create(case=case, actor=request.user, action="escalated")
        notification_services.notify_victim(case)
    return redirect("cases:detail", pk=pk)
