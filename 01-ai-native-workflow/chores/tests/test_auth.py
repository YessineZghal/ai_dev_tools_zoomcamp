from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from chores.models import Household, Membership, household_of


class RegisterTests(TestCase):
    def test_register_creates_household_and_logs_in(self):
        response = self.client.post(
            reverse("register"),
            {
                "username": "ana",
                "password1": "chore-pass-123",
                "password2": "chore-pass-123",
                "mode": "create",
                "household_name": "Flat A",
            },
        )
        self.assertRedirects(response, reverse("dashboard"))
        user = User.objects.get(username="ana")
        household = household_of(user)
        self.assertIsNotNone(household)
        self.assertEqual(household.name, "Flat A")
        self.assertEqual(household.members.count(), 1)
        # session is authenticated
        self.assertEqual(int(self.client.session["_auth_user_id"]), user.pk)

    def test_register_joins_existing_household_by_code(self):
        existing = Household.objects.create(name="Flat B")
        response = self.client.post(
            reverse("register"),
            {
                "username": "bo",
                "password1": "chore-pass-123",
                "password2": "chore-pass-123",
                "mode": "join",
                "invite_code": existing.invite_code,
            },
        )
        self.assertRedirects(response, reverse("dashboard"))
        user = User.objects.get(username="bo")
        self.assertEqual(household_of(user), existing)

    def test_register_join_code_is_case_insensitive(self):
        existing = Household.objects.create(name="Flat B")
        response = self.client.post(
            reverse("register"),
            {
                "username": "cy",
                "password1": "chore-pass-123",
                "password2": "chore-pass-123",
                "mode": "join",
                "invite_code": existing.invite_code.lower(),
            },
        )
        self.assertRedirects(response, reverse("dashboard"))
        self.assertEqual(household_of(User.objects.get(username="cy")), existing)

    def test_register_join_bad_code_rejected(self):
        response = self.client.post(
            reverse("register"),
            {
                "username": "dee",
                "password1": "chore-pass-123",
                "password2": "chore-pass-123",
                "mode": "join",
                "invite_code": "ZZZZZZ",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(username="dee").exists())
        self.assertContains(response, "invite code", status_code=200)

    def test_register_create_without_name_rejected(self):
        response = self.client.post(
            reverse("register"),
            {
                "username": "eve",
                "password1": "chore-pass-123",
                "password2": "chore-pass-123",
                "mode": "create",
                "household_name": "",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(username="eve").exists())


class LoginLogoutTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user("ana", password="chore-pass-123")
        household = Household.objects.create(name="Flat A")
        Membership.objects.create(
            user=self.user, household=household, display_name="ana"
        )

    def test_dashboard_requires_login(self):
        response = self.client.get(reverse("dashboard"))
        self.assertRedirects(
            response, f"{reverse('login')}?next={reverse('dashboard')}"
        )

    def test_login_then_dashboard(self):
        self.client.login(username="ana", password="chore-pass-123")
        response = self.client.get(reverse("dashboard"))
        self.assertEqual(response.status_code, 200)

    def test_logout(self):
        self.client.login(username="ana", password="chore-pass-123")
        response = self.client.post(reverse("logout"))
        self.assertEqual(response.status_code, 302)
        self.assertNotIn("_auth_user_id", self.client.session)


class HouseholdSetupTests(TestCase):
    def test_logged_in_user_without_membership_redirected_to_setup(self):
        User.objects.create_user("lonely", password="chore-pass-123")
        self.client.login(username="lonely", password="chore-pass-123")
        response = self.client.get(reverse("dashboard"))
        self.assertRedirects(response, reverse("household_setup"))

    def test_setup_create_household(self):
        User.objects.create_user("lonely", password="chore-pass-123")
        self.client.login(username="lonely", password="chore-pass-123")
        response = self.client.post(
            reverse("household_setup"),
            {"mode": "create", "household_name": "New Home"},
        )
        self.assertRedirects(response, reverse("dashboard"))
        user = User.objects.get(username="lonely")
        self.assertEqual(household_of(user).name, "New Home")
