# notifications/services.py
"""Sending + audit for case notifications.

Every notification that leaves the system is recorded as a `Notification`
row (channel, recipient, status, and the exact message sent) so it can be
audited later.

Survivor notifications are deliberately neutral: someone else might be
looking at the survivor's screen when a push or email arrives, so we never
echo case content or details.
"""

import json
import logging

from django.conf import settings
from django.core.mail import send_mail

from accounts.models import User
from .models import Notification, PushSubscription

logger = logging.getLogger(__name__)

PUSH_TTL = 0  # 0 = deliver immediately, don't queue on the push service

SURVIVOR_NUDGE = (
    "Your report {reference_number} has an update. "
    "You can check it anytime with your tracking code."
)
STAFF_REPLY_ALERT = "A survivor sent a message on case {reference_number}."


def _record(case, channel, message, *, update=None, recipient_user=None,
            status=Notification.Status.SENT, error_detail=""):
    return Notification.objects.create(
        case=case,
        update=update,
        recipient_user=recipient_user,
        channel=channel,
        status=status,
        message=message,
        error_detail=error_detail,
    )


def _send_webpush(subscription, title, body, url):
    """Deliver one web push to a single subscription.

    Returns (ok, error). Stale subscriptions (HTTP 404/410) are dropped.
    """
    if not (settings.VAPID_PRIVATE_KEY and settings.VAPID_PUBLIC_KEY):
        return False, "VAPID keys not configured"

    from pywebpush import WebPushException, webpush

    try:
        webpush(
            subscription_info={
                "endpoint": subscription.endpoint,
                "keys": {
                    "p256dh": subscription.p256dh_key,
                    "auth": subscription.auth_key,
                },
            },
            data=json.dumps({"title": title, "body": body, "url": url}),
            vapid_private_key=settings.VAPID_PRIVATE_KEY,
            vapid_claims={"sub": f"mailto:{settings.VAPID_ADMIN_EMAIL}"},
            ttl=PUSH_TTL,
        )
        return True, ""
    except WebPushException as exc:
        response = getattr(exc, "response", None)
        if response is not None and response.status_code in (404, 410):
            subscription.delete()
            return False, "subscription expired"
        return False, str(exc)
    except Exception:  # noqa: BLE001 - don't let one bad send break the request
        logger.exception("Unexpected web push failure")
        return False, "unexpected error"


def notify_victim(case, update=None):
    """Notify the survivor that their case has been updated.

    Sends via every channel the survivor opted into (web push to any
    subscribed devices, email if chosen). SMS is recorded as failed because
    no gateway is wired up yet.
    """
    message = SURVIVOR_NUDGE.format(reference_number=case.reference_number)
    url = "/track/"

    for subscription in PushSubscription.objects.filter(case=case):
        ok, error = _send_webpush(subscription, "Amani update", message, url)
        _record(
            case, Notification.Channel.PUSH, message, update=update,
            status=Notification.Status.SENT if ok else Notification.Status.FAILED,
            error_detail=error,
        )

    if case.contact_method == case.ContactMethod.EMAIL and case.contact_value:
        subject = "Amani update on your report"
        body = (
            f"{message}\n\n"
            f"Your reference number is {case.reference_number}. "
            "You can check updates anytime with your tracking code."
        )
        try:
            send_mail(
                subject=subject,
                message=body,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[case.contact_value],
                fail_silently=False,
            )
            _record(case, Notification.Channel.EMAIL, message, update=update)
        except Exception:  # noqa: BLE001
            logger.exception("Email notification failed")
            _record(
                case, Notification.Channel.EMAIL, message, update=update,
                status=Notification.Status.FAILED, error_detail="email send failed",
            )

    if case.contact_method == case.ContactMethod.PHONE and case.contact_value:
        _record(
            case, Notification.Channel.SMS, message, update=update,
            status=Notification.Status.FAILED, error_detail="SMS gateway not configured",
        )


def notify_staff(case, update=None):
    """Alert the people handling the case that the survivor has replied.

    Targets the assigned case handler, falling back to all supervisors when
    the case is unassigned.
    """
    message = STAFF_REPLY_ALERT.format(reference_number=case.reference_number)
    url = f"/staff/cases/{case.pk}/"

    if case.assigned_handler_id:
        targets = User.objects.filter(
            id=case.assigned_handler_id, is_active=True, role=User.Role.CASE_HANDLER
        )
    else:
        targets = User.objects.filter(is_active=True, role=User.Role.SUPERVISOR)

    for user in targets:
        for subscription in user.push_subscriptions.all():
            ok, error = _send_webpush(subscription, "Amani — new survivor message", message, url)
            _record(
                case, Notification.Channel.PUSH, message, update=update,
                recipient_user=user,
                status=Notification.Status.SENT if ok else Notification.Status.FAILED,
                error_detail=error,
            )

        if user.email:
            try:
                send_mail(
                    subject="Amani — new survivor message",
                    message=f"{message}\n\nView the case: {url}",
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[user.email],
                    fail_silently=False,
                )
                _record(
                    case, Notification.Channel.EMAIL, message, update=update,
                    recipient_user=user,
                )
            except Exception:  # noqa: BLE001
                logger.exception("Staff email notification failed")
                _record(
                    case, Notification.Channel.EMAIL, message, update=update,
                    recipient_user=user, status=Notification.Status.FAILED,
                    error_detail="email send failed",
                )
