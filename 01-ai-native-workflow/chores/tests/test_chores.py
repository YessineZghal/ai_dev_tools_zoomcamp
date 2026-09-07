from datetime import date

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from chores.models import Assignment, Chore, Household, Membership


def make_household(name, username):
    household = Household.objects.create(name=name)
    user = User.objects.create_user(username, password="chore-pass-123")
    Membership.objects.create(user=user, household=household, display_name=username)
    return household, user


class ChoreCrudTests(TestCase):
    def setUp(self):
        self.hh_a, self.ana = make_household("Flat A", "ana")
        self.hh_b, self.bo = make_household("Flat B", "bo")
        self.client.login(username="ana", password="chore-pass-123")

    def test_list_shows_only_my_household_chores(self):
        Chore.objects.create(household=self.hh_a, title="A-dishes")
        Chore.objects.create(household=self.hh_b, title="B-trash")
        response = self.client.get(reverse("chore_list"))
        self.assertContains(response, "A-dishes")
        self.assertNotContains(response, "B-trash")

    def test_create_chore_attaches_my_household(self):
        response = self.client.post(
            reverse("chore_create"),
            {"title": "Vacuum", "description": "", "points": 5, "is_active": "on"},
        )
        self.assertRedirects(response, reverse("chore_list"))
        chore = Chore.objects.get(title="Vacuum")
        self.assertEqual(chore.household, self.hh_a)
        self.assertEqual(chore.points, 5)

    def test_update_chore(self):
        chore = Chore.objects.create(household=self.hh_a, title="Old", points=1)
        response = self.client.post(
            reverse("chore_update", args=[chore.pk]),
            {"title": "New", "description": "now tidier", "points": 3, "is_active": "on"},
        )
        self.assertRedirects(response, reverse("chore_list"))
        chore.refresh_from_db()
        self.assertEqual(chore.title, "New")
        self.assertEqual(chore.points, 3)

    def test_delete_chore_removes_assignments(self):
        chore = Chore.objects.create(household=self.hh_a, title="Gone")
        Assignment.objects.create(chore=chore, assignee=self.ana, due_date=date.today())
        response = self.client.post(reverse("chore_delete", args=[chore.pk]))
        self.assertRedirects(response, reverse("chore_list"))
        self.assertFalse(Chore.objects.filter(pk=chore.pk).exists())
        self.assertEqual(Assignment.objects.count(), 0)

    def test_cannot_view_edit_form_for_other_household_chore(self):
        chore_b = Chore.objects.create(household=self.hh_b, title="B-only")
        self.assertEqual(
            self.client.get(reverse("chore_update", args=[chore_b.pk])).status_code, 404
        )

    def test_cannot_post_edit_to_other_household_chore(self):
        chore_b = Chore.objects.create(household=self.hh_b, title="B-only")
        response = self.client.post(
            reverse("chore_update", args=[chore_b.pk]),
            {"title": "hacked", "points": 1, "is_active": "on"},
        )
        self.assertEqual(response.status_code, 404)
        chore_b.refresh_from_db()
        self.assertEqual(chore_b.title, "B-only")

    def test_cannot_delete_other_household_chore(self):
        chore_b = Chore.objects.create(household=self.hh_b, title="B-only")
        response = self.client.post(reverse("chore_delete", args=[chore_b.pk]))
        self.assertEqual(response.status_code, 404)
        self.assertTrue(Chore.objects.filter(pk=chore_b.pk).exists())

    def test_list_requires_login(self):
        self.client.logout()
        response = self.client.get(reverse("chore_list"))
        self.assertEqual(response.status_code, 302)
        self.assertIn("/accounts/login/", response["Location"])

    def test_list_shows_none_when_only_finished_assignments(self):
        chore = Chore.objects.create(household=self.hh_a, title="Done-only")
        done = Assignment.objects.create(
            chore=chore, assignee=self.ana, due_date=date.today()
        )
        done.complete(self.ana)
        skipped = Assignment.objects.create(
            chore=chore, assignee=self.ana, due_date=date.today()
        )
        skipped.skip()
        response = self.client.get(reverse("chore_list"))
        self.assertContains(response, "Done-only")
        # the finished assignments are not listed as open work
        self.assertNotContains(response, "due {}".format(date.today()))
