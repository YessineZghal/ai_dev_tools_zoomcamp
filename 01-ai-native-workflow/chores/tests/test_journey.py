"""End-to-end walk through the flow described in the README's success criteria."""

from datetime import date

from django.test import TestCase
from django.urls import reverse

from chores.models import Assignment, Chore, CompletionEvent, Household


class HouseholdJourneyTests(TestCase):
    def test_full_flow_two_members(self):
        # 1. Ana registers and creates a household.
        self.client.post(
            reverse("register"),
            {
                "username": "ana",
                "password1": "chore-pass-123",
                "password2": "chore-pass-123",
                "mode": "create",
                "household_name": "Maple Street",
            },
        )
        household = Household.objects.get(name="Maple Street")

        # 2. Ana adds a chore.
        self.client.post(
            reverse("chore_create"),
            {"title": "Take out recycling", "description": "", "points": 2,
             "is_active": "on"},
        )
        chore = Chore.objects.get(title="Take out recycling")

        # 3. Ana assigns it to herself, due today.
        self.client.post(
            reverse("assignment_create", args=[chore.pk]),
            {"assignee": self.client.session["_auth_user_id"],
             "due_date": date.today().isoformat()},
        )
        assignment = Assignment.objects.get()

        # 4. Ana completes it.
        self.client.post(reverse("assignment_complete", args=[assignment.pk]))
        assignment.refresh_from_db()
        self.assertEqual(assignment.status, Assignment.Status.DONE)
        self.assertEqual(CompletionEvent.objects.count(), 1)

        # 5. Dashboard shows the completion and no pending items.
        dashboard = self.client.get(reverse("dashboard"))
        self.assertContains(dashboard, "Take out recycling")
        self.assertEqual(list(dashboard.context["my_pending"]), [])
        board = {r["member"].username: r["points"] for r in dashboard.context["leaderboard"]}
        self.assertEqual(board["ana"], 2)

        # 6. History records it.
        history = self.client.get(reverse("history"))
        self.assertContains(history, "Take out recycling")

        # 7. Bo joins the same household with the invite code and sees it too.
        self.client.logout()
        self.client.post(
            reverse("register"),
            {
                "username": "bo",
                "password1": "chore-pass-123",
                "password2": "chore-pass-123",
                "mode": "join",
                "invite_code": household.invite_code.lower(),
            },
        )
        bo_history = self.client.get(reverse("history"))
        self.assertContains(bo_history, "Take out recycling")
        self.assertEqual(household.members.count(), 2)
