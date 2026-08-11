from django.shortcuts import render, get_object_or_404, redirect
from accounts.decorators import role_required
from .models import CaseReport, CaseAuditLog

@role_required("case_handler", "supervisor")
def dashboard(request):
    if request.user.role == "supervisor":
        cases = CaseReport.objects.all().order_by("-created_at")
    else:
        cases = CaseReport.objects.filter(assigned_handler=request.user).order_by("-created_at")
    return render(request, "cases/dashboard.html", {"cases": cases})

@role_required("case_handler", "supervisor")
def case_detail(request, pk):
    case = get_object_or_404(CaseReport, pk=pk)
    if request.user.role == "case_handler" and case.assigned_handler_id != request.user.id:
        from django.core.exceptions import PermissionDenied
        raise PermissionDenied
    return render(request, "cases/detail.html", {"case": case})

@role_required("case_handler", "supervisor")
def update_status(request, pk):
    case = get_object_or_404(CaseReport, pk=pk)
    if request.method == "POST":
        new_status = request.POST.get("status")
        case.status = new_status
        case.save()
        CaseAuditLog.objects.create(case=case, actor=request.user, action="status_changed", detail=new_status)
        # trigger notification if contact info exists — see notifications app
    return redirect("cases:detail", pk=pk)

@role_required("supervisor")
def escalate(request, pk):
    case = get_object_or_404(CaseReport, pk=pk)
    if request.method == "POST":
        case.status = CaseReport.Status.ESCALATED
        case.save()
        CaseAuditLog.objects.create(case=case, actor=request.user, action="escalated")
    return redirect("cases:detail", pk=pk)