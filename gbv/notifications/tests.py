# notifications/tests.py
from types import SimpleNamespace
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core import mail
from django.test import TestCase

from accounts.models import User
from cases.models import CaseReport, CaseUpdate, Category
from pywebpush import WebPushException

from .models import Notification, PushSubscription


class NotificationTestCase(TestCase):
    def setUp(self):
        self.handler = User.objects.create_user(
            username="handler", password="pass12345", role="case_handler", email="handler@amani.local"
        )
        self.supervisor = User.objects.create_user(
            username="super", password="pass12345", role="supervisor", email="super@amani.local"
        )
        self.category = Category.objects.create(name="Online Harassment")
        self.case = CaseReport.objects.create(
            category=self.category, description="test", assigned_handler=self.handler
        )
        self.case.set_tracking_code("AB23CD45")
        self.case.save()

    def _subscribe_victim(self, endpoint="https://push.example.com/one"):
        return PushSubscription.objects.create(
            case=self.case, endpoint=endpoint, p256dh_key="abc", auth_key="def"
        )

    def _subscribe_staff(self, user, endpoint="https://push.example.com/staff"):
        return PushSubscription.objects.create(
            user=user, endpoint=endpoint, p256dh_key="abc", auth_key="def"
        )


class VictimNotificationTests(NotificationTestCase):
    @patch("pywebpush.webpush")
    def test_status_update_sends_push_and_email(self, mock_push):
        self.case.contact_method = CaseReport.ContactMethod.EMAIL
        self.case.contact_value = "victim@example.com"
        self.case.save()
        sub = self._subscribe_victim()

        self.client.login(username="handler", password="pass12345")
        self.client.post(
            f"/staff/cases/{self.case.pk}/status/",
            {"status": "under_review"},
        )

        self.assertEqual(mock_push.call_count, 1)
        payload = mock_push.call_args.kwargs["data"]
        self.assertIn(self.case.reference_number, payload)
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("victim@example.com", mail.outbox[0].to)

        sent = Notification.objects.filter(channel="push", status="sent")
        self.assertEqual(sent.count(), 1)
        self.assertEqual(sent.first().case_id, self.case.pk)
        self.assertIsNone(sent.first().recipient_user)

    @patch("pywebpush.webpush")
    def test_stale_subscription_is_dropped(self, mock_push):
        sub = self._subscribe_victim()
        mock_push.side_effect = WebPushException(
            "gone", response=SimpleNamespace(status_code=410)
        )

        self.client.login(username="handler", password="pass12345")
        self.client.post(
            f"/staff/cases/{self.case.pk}/status/",
            {"status": "closed"},
        )

        self.assertFalse(PushSubscription.objects.filter(pk=sub.pk).exists())
        failed = Notification.objects.filter(channel="push", status="failed")
        self.assertEqual(failed.count(), 1)
        self.assertEqual(failed.first().error_detail, "subscription expired")

    @patch("pywebpush.webpush")
    def test_handler_update_notifies_victim_only_when_visible(self, mock_push):
        self._subscribe_victim()
        self.client.login(username="handler", password="pass12345")

        self.client.post(
            f"/staff/cases/{self.case.pk}/update/",
            {"message": "internal only", "visibility": "internal"},
        )
        self.assertEqual(mock_push.call_count, 0)

        self.client.post(
            f"/staff/cases/{self.case.pk}/update/",
            {"message": "we're looking into it", "visibility": "victim"},
        )
        self.assertEqual(mock_push.call_count, 1)
        update = CaseUpdate.objects.filter(author_type="handler").get(visibility="victim")
        self.assertIsNotNone(Notification.objects.filter(update=update).first())

    def test_phone_contact_records_failed_sms(self):
        self.case.contact_method = CaseReport.ContactMethod.PHONE
        self.case.contact_value = "+254700000000"
        self.case.save()

        self.client.login(username="handler", password="pass12345")
        self.client.post(
            f"/staff/cases/{self.case.pk}/status/",
            {"status": "resolved"},
        )

        sms = Notification.objects.filter(channel="sms").first()
        self.assertIsNotNone(sms)
        self.assertEqual(sms.status, "failed")
        self.assertEqual(sms.error_detail, "SMS gateway not configured")


class StaffNotificationTests(NotificationTestCase):
    @patch("pywebpush.webpush")
    def test_victim_reply_notifies_assigned_handler(self, mock_push):
        sub = self._subscribe_staff(self.handler)
        self.client.post(
            f"/track/{self.case.pk}/reply/",
            {
                "reference_number": self.case.reference_number,
                "tracking_code": "AB23CD45",
                "message": "hello",
            },
        )

        self.assertEqual(mock_push.call_count, 1)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, ["handler@amani.local"])

        note = Notification.objects.filter(recipient_user=self.handler).first()
        self.assertIsNotNone(note)
        self.assertEqual(note.status, "sent")

    @patch("pywebpush.webpush")
    def test_reply_to_unassigned_case_notifies_supervisors(self, mock_push):
        self.case.assigned_handler = None
        self.case.save()
        super_sub = self._subscribe_staff(self.supervisor, endpoint="https://push.example.com/sup")
        handler_sub = self._subscribe_staff(self.handler, endpoint="https://push.example.com/h")

        self.client.post(
            f"/track/{self.case.pk}/reply/",
            {
                "reference_number": self.case.reference_number,
                "tracking_code": "AB23CD45",
                "message": "hello",
            },
        )

        self.assertEqual(mock_push.call_count, 1)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, ["super@amani.local"])
        self.assertTrue(handler_sub.pk is not None)
        self.assertTrue(super_sub.pk is not None)
