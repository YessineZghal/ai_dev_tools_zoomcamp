from datetime import date, timedelta

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from chores.models import Assignment, Chore, CompletionEvent, Household, Membership


def make_household(name, username):
    household = Household.objects.create(name=name)
    user = User.objects.create_user(username, password="chore-pass-123")
    Membership.objects.create(user=user, household=household, display_name=username)
    return household, user


class AssignmentViewTests(TestCase):
    def setUp(self):
        self.hh_a, self.ana = make_household("Flat A", "ana")
        self.bea = User.objects.create_user("bea", password="chore-pass-123")
        Membership.objects.create(
            user=self.bea, household=self.hh_a, display_name="bea"
        )
        self.hh_b, self.zed = make_household("Flat B", "zed")
        self.chore = Chore.objects.create(household=self.hh_a, title="Dishes", points=4)
        self.client.login(username="ana", password="chore-pass-123")

    def test_assign_form_limits_assignee_to_household(self):
        response = self.client.get(reverse("assignment_create", args=[self.chore.pk]))
        form = response.context["form"]
        assignees = set(form.fields["assignee"].queryset)
        self.assertEqual(assignees, {self.ana, self.bea})
        self.assertNotIn(self.zed, assignees)

    def test_assign_creates_pending_assignment(self):
        due = date.today() + timedelta(days=2)
        response = self.client.post(
            reverse("assignment_create", args=[self.chore.pk]),
            {"assignee": self.bea.pk, "due_date": due.isoformat()},
        )
        self.assertRedirects(response, reverse("chore_list"))
        assignment = Assignment.objects.get()
        self.assertEqual(assignment.chore, self.chore)
        self.assertEqual(assignment.assignee, self.bea)
        self.assertEqual(assignment.due_date, due)
        self.assertEqual(assignment.status, Assignment.Status.PENDING)

    def test_assign_rejects_outside_household_user(self):
        response = self.client.post(
            reverse("assignment_create", args=[self.chore.pk]),
            {"assignee": self.zed.pk, "due_date": date.today().isoformat()},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Assignment.objects.count(), 0)

    def test_complete_assignment_records_event(self):
        assignment = Assignment.objects.create(
            chore=self.chore, assignee=self.bea, due_date=date.today()
        )
        response = self.client.post(
            reverse("assignment_complete", args=[assignment.pk])
        )
        self.assertEqual(response.status_code, 302)
        assignment.refresh_from_db()
        self.assertEqual(assignment.status, Assignment.Status.DONE)
        event = CompletionEvent.objects.get()
        self.assertEqual(event.completed_by, self.ana)
        self.assertEqual(event.points_awarded, 4)

    def test_skip_assignment_no_event(self):
        assignment = Assignment.objects.create(
            chore=self.chore, assignee=self.bea, due_date=date.today()
        )
        response = self.client.post(reverse("assignment_skip", args=[assignment.pk]))
        self.assertEqual(response.status_code, 302)
        assignment.refresh_from_db()
        self.assertEqual(assignment.status, Assignment.Status.SKIPPED)
        self.assertEqual(CompletionEvent.objects.count(), 0)

    def test_complete_rejects_get(self):
        assignment = Assignment.objects.create(
            chore=self.chore, assignee=self.bea, due_date=date.today()
        )
        response = self.client.get(reverse("assignment_complete", args=[assignment.pk]))
        self.assertEqual(response.status_code, 405)

    def test_cannot_complete_other_household_assignment(self):
        other_chore = Chore.objects.create(household=self.hh_b, title="B-dishes")
        other = Assignment.objects.create(
            chore=other_chore, assignee=self.zed, due_date=date.today()
        )
        response = self.client.post(reverse("assignment_complete", args=[other.pk]))
        self.assertEqual(response.status_code, 404)
        other.refresh_from_db()
        self.assertEqual(other.status, Assignment.Status.PENDING)

    def test_complete_honours_local_next(self):
        assignment = Assignment.objects.create(
            chore=self.chore, assignee=self.bea, due_date=date.today()
        )
        response = self.client.post(
            reverse("assignment_complete", args=[assignment.pk]),
            {"next": reverse("chore_list")},
        )
        self.assertRedirects(response, reverse("chore_list"))

    def test_complete_ignores_offsite_next(self):
        assignment = Assignment.objects.create(
            chore=self.chore, assignee=self.bea, due_date=date.today()
        )
        response = self.client.post(
            reverse("assignment_complete", args=[assignment.pk]),
            {"next": "https://evil.example/"},
        )
        self.assertRedirects(response, reverse("dashboard"))
