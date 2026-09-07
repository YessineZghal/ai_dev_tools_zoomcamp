from datetime import date, timedelta

from django.contrib.auth.models import User
from django.test import TestCase
from django.utils import timezone

from chores.models import (
    Assignment,
    Chore,
    CompletionEvent,
    Household,
    Membership,
    household_of,
)


class HouseholdModelTests(TestCase):
    def test_invite_code_generated_and_unique(self):
        h1 = Household.objects.create(name="Flat A")
        h2 = Household.objects.create(name="Flat B")
        self.assertEqual(len(h1.invite_code), 6)
        self.assertTrue(h1.invite_code.isalnum())
        self.assertEqual(h1.invite_code, h1.invite_code.upper())
        self.assertNotEqual(h1.invite_code, h2.invite_code)

    def test_invite_code_is_stable_across_saves(self):
        h = Household.objects.create(name="Flat A")
        original = h.invite_code
        h.name = "Renamed"
        h.save()
        h.refresh_from_db()
        self.assertEqual(h.invite_code, original)

    def test_members_and_household_of(self):
        h = Household.objects.create(name="Flat A")
        u = User.objects.create_user("ana", password="x")
        Membership.objects.create(user=u, household=h, display_name="Ana")
        self.assertIn(u, list(h.members))
        self.assertEqual(household_of(u), h)

    def test_household_of_returns_none_without_membership(self):
        u = User.objects.create_user("no_home", password="x")
        self.assertIsNone(household_of(u))


class ChoreModelTests(TestCase):
    def test_defaults(self):
        h = Household.objects.create(name="Flat A")
        chore = Chore.objects.create(household=h, title="Dishes")
        self.assertEqual(chore.points, 1)
        self.assertTrue(chore.is_active)
        self.assertEqual(str(chore), "Dishes")


class AssignmentModelTests(TestCase):
    def setUp(self):
        self.h = Household.objects.create(name="Flat A")
        self.u = User.objects.create_user("ana", password="x")
        Membership.objects.create(user=self.u, household=self.h, display_name="Ana")
        self.chore = Chore.objects.create(household=self.h, title="Dishes", points=3)

    def test_default_status_is_pending(self):
        a = Assignment.objects.create(
            chore=self.chore, assignee=self.u, due_date=date.today()
        )
        self.assertEqual(a.status, Assignment.Status.PENDING)

    def test_is_overdue_true_when_pending_and_past(self):
        a = Assignment.objects.create(
            chore=self.chore,
            assignee=self.u,
            due_date=date.today() - timedelta(days=1),
        )
        self.assertTrue(a.is_overdue())

    def test_is_overdue_false_when_due_today(self):
        a = Assignment.objects.create(
            chore=self.chore, assignee=self.u, due_date=date.today()
        )
        self.assertFalse(a.is_overdue())

    def test_is_overdue_false_when_done(self):
        a = Assignment.objects.create(
            chore=self.chore,
            assignee=self.u,
            due_date=date.today() - timedelta(days=1),
            status=Assignment.Status.DONE,
        )
        self.assertFalse(a.is_overdue())

    def test_complete_creates_event_and_sets_status(self):
        a = Assignment.objects.create(
            chore=self.chore, assignee=self.u, due_date=date.today()
        )
        event = a.complete(self.u, note="sparkling")
        a.refresh_from_db()
        self.assertEqual(a.status, Assignment.Status.DONE)
        self.assertIsNotNone(a.completed_at)
        self.assertEqual(event.points_awarded, 3)
        self.assertEqual(event.completed_by, self.u)
        self.assertEqual(event.note, "sparkling")
        self.assertEqual(CompletionEvent.objects.count(), 1)

    def test_complete_is_idempotent_no_duplicate_events(self):
        a = Assignment.objects.create(
            chore=self.chore, assignee=self.u, due_date=date.today()
        )
        a.complete(self.u)
        a.complete(self.u)
        self.assertEqual(CompletionEvent.objects.count(), 1)

    def test_skip_sets_status_and_no_event(self):
        a = Assignment.objects.create(
            chore=self.chore, assignee=self.u, due_date=date.today()
        )
        a.skip()
        a.refresh_from_db()
        self.assertEqual(a.status, Assignment.Status.SKIPPED)
        self.assertEqual(CompletionEvent.objects.count(), 0)

    def test_deleting_chore_cascades_to_assignments(self):
        Assignment.objects.create(
            chore=self.chore, assignee=self.u, due_date=date.today()
        )
        self.chore.delete()
        self.assertEqual(Assignment.objects.count(), 0)
