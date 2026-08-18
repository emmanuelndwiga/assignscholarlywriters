from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model

from cases.models import Category, CaseReport


class UISmokeTest(TestCase):
    def setUp(self):
        User = get_user_model()
        self.handler = User.objects.create_user(
            username="handler", password="pass12345", role="case_handler"
        )
        self.supervisor = User.objects.create_user(
            username="super", password="pass12345", role="supervisor"
        )
        self.category = Category.objects.create(name="Online Harassment")
        self.case = CaseReport.objects.create(
            category=self.category, description="test description"
        )
        self.case.set_tracking_code("AB23CD45")
        self.case.save()
        self.ref = self.case.reference_number

    def test_public_pages_render(self):
        self.assertEqual(self.client.get(reverse("public:landing")).status_code, 200)
        self.assertEqual(self.client.get(reverse("public:submit")).status_code, 200)
        self.assertEqual(self.client.get(reverse("public:track")).status_code, 200)

    def test_submit_and_confirmation_render(self):
        resp = self.client.post(
            reverse("public:submit"),
            {"category": self.category.id, "description": "something happened"},
        )
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Reference number")
        self.assertContains(resp, "Tracking code")

    def test_track_and_status_with_progress_render(self):
        resp = self.client.post(
            reverse("public:track"),
            {"reference_number": self.ref, "tracking_code": "AB23CD45"},
        )
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "progress-track")

    def test_staff_pages_render(self):
        resp = self.client.get(reverse("accounts:login"))
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(self.client.login(username="handler", password="pass12345"))
        resp = self.client.get(reverse("cases:dashboard"))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, self.ref)
        resp = self.client.get(reverse("cases:detail", args=[self.case.pk]))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Audit trail")

    def test_supervisor_invite_page_render(self):
        self.client.login(username="super", password="pass12345")
        resp = self.client.get(reverse("accounts:create_handler"))
        self.assertEqual(resp.status_code, 200)

    def test_status_update_flow(self):
        self.client.login(username="handler", password="pass12345")
        resp = self.client.post(
            reverse("cases:update_status", args=[self.case.pk]),
            {"status": "under_review"},
        )
        self.assertEqual(resp.status_code, 302)
        self.case.refresh_from_db()
        self.assertEqual(self.case.status, "under_review")
