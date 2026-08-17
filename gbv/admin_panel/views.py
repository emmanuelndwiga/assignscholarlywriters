from django.shortcuts import render
from django.contrib.auth import get_user_model
from django.db.models import Count, Q
from django.utils import timezone
from datetime import timedelta

from accounts.decorators import role_required
from cases.models import CaseReport, Category

User = get_user_model()


@role_required("supervisor")
def overview(request):
    now = timezone.now()
    thirty_days_ago = now - timedelta(days=30)
    today = now.date()

    total_cases = CaseReport.objects.count()
    pending_review = CaseReport.objects.filter(status="submitted").count()
    under_review = CaseReport.objects.filter(status="under_review").count()
    escalated = CaseReport.objects.filter(status="escalated").count()
    resolved_today = CaseReport.objects.filter(
        status="resolved", updated_at__date=today
    ).count()
    total_users = User.objects.count()
    active_users = User.objects.filter(
        last_login__gte=thirty_days_ago
    ).count()

    recent_cases = CaseReport.objects.select_related("category", "assigned_handler").order_by(
        "-created_at"
    )[:10]

    category_counts = (
        CaseReport.objects.filter(created_at__gte=thirty_days_ago)
        .values("category__name")
        .annotate(count=Count("id"))
        .order_by("-count")
    )

    status_counts = (
        CaseReport.objects.filter(created_at__gte=thirty_days_ago)
        .values("status")
        .annotate(count=Count("id"))
        .order_by("-count")
    )

    context = {
        "active_page": "overview",
        "total_cases": total_cases,
        "pending_review": pending_review,
        "under_review": under_review,
        "escalated": escalated,
        "resolved_today": resolved_today,
        "total_users": total_users,
        "active_users": active_users,
        "recent_cases": recent_cases,
        "category_counts": category_counts,
        "status_counts": status_counts,
    }
    return render(request, "admin/overview.html", context)


@role_required("supervisor")
def users(request):
    users_list = User.objects.all().order_by("-date_joined")
    total_users = users_list.count()
    active_users = User.objects.filter(is_active=True).count()
    supervisor_count = User.objects.filter(role="supervisor").count()

    role_filter = request.GET.get("role", "")
    status_filter = request.GET.get("status", "")
    search_query = request.GET.get("q", "").strip()

    if role_filter:
        users_list = users_list.filter(role=role_filter)
    if status_filter == "active":
        users_list = users_list.filter(is_active=True)
    elif status_filter == "inactive":
        users_list = users_list.filter(is_active=False)
    if search_query:
        users_list = users_list.filter(
            Q(username__icontains=search_query)
            | Q(email__icontains=search_query)
            | Q(first_name__icontains=search_query)
            | Q(last_name__icontains=search_query)
        )

    context = {
        "active_page": "users",
        "users_list": users_list,
        "total_users": total_users,
        "active_users": active_users,
        "supervisor_count": supervisor_count,
        "role_filter": role_filter,
        "status_filter": status_filter,
        "search_query": search_query,
    }
    return render(request, "admin/users.html", context)


@role_required("supervisor")
def analytics(request):
    now = timezone.now()
    thirty_days_ago = now - timedelta(days=30)
    sixty_days_ago = now - timedelta(days=60)

    current_period = CaseReport.objects.filter(created_at__gte=thirty_days_ago)
    previous_period = CaseReport.objects.filter(
        created_at__gte=sixty_days_ago, created_at__lt=thirty_days_ago
    )

    total_current = current_period.count()
    total_previous = previous_period.count()
    total_change = total_current - total_previous
    total_change_pct = (
        round((total_change / total_previous * 100), 1) if total_previous > 0 else 0
    )

    critical_current = current_period.filter(status="escalated").count()
    critical_previous = previous_period.filter(status="escalated").count()
    critical_change = critical_current - critical_previous

    resolved_current = current_period.filter(status__in=["resolved", "closed"]).count()
    resolution_rate = (
        round((resolved_current / total_current * 100), 1) if total_current > 0 else 0
    )

    category_breakdown = (
        current_period.values("category__name")
        .annotate(count=Count("id"))
        .order_by("-count")
    )

    status_breakdown = (
        current_period.values("status")
        .annotate(count=Count("id"))
        .order_by("-count")
    )

    platform_breakdown = (
        current_period.exclude(platform="")
        .exclude(platform="n/a")
        .values("platform")
        .annotate(count=Count("id"))
        .order_by("-count")
    )

    context = {
        "active_page": "analytics",
        "total_incidents": total_current,
        "total_change_pct": abs(total_change_pct),
        "total_change": total_change,
        "critical_alerts": critical_current,
        "critical_change": critical_change,
        "critical_change_abs": abs(critical_change),
        "resolution_rate": resolution_rate,
        "category_breakdown": category_breakdown,
        "status_breakdown": status_breakdown,
        "platform_breakdown": platform_breakdown,
        "total_previous": total_previous,
    }
    return render(request, "admin/analytics.html", context)


@role_required("supervisor")
def reports(request):
    cases = CaseReport.objects.select_related(
        "category", "assigned_handler"
    ).order_by("-created_at")

    status_filter = request.GET.get("status", "")
    category_filter = request.GET.get("category", "")
    search_query = request.GET.get("q", "").strip()

    if status_filter:
        cases = cases.filter(status=status_filter)
    if category_filter:
        cases = cases.filter(category__id=category_filter)
    if search_query:
        cases = cases.filter(
            Q(reference_number__icontains=search_query)
            | Q(description__icontains=search_query)
            | Q(perpetrator_name__icontains=search_query)
        )

    categories = Category.objects.filter(is_active=True)

    context = {
        "active_page": "reports",
        "cases": cases,
        "categories": categories,
        "status_filter": status_filter,
        "category_filter": category_filter,
        "search_query": search_query,
    }
    return render(request, "admin/reports.html", context)
