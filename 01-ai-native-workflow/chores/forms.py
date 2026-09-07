from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

from .models import Assignment, Chore, Household, Membership


class HouseholdChoiceForm(forms.Form):
    """Lets a user create a brand-new household or join one with an invite code.

    Used standalone on the "set up your household" page and mixed into
    ``RegisterForm`` so a new account lands in a household immediately.
    """

    MODE_CHOICES = [
        ("create", "Create a new household"),
        ("join", "Join an existing household with an invite code"),
    ]

    mode = forms.ChoiceField(
        choices=MODE_CHOICES, widget=forms.RadioSelect, initial="create"
    )
    household_name = forms.CharField(
        max_length=100, required=False, label="Household name"
    )
    invite_code = forms.CharField(
        max_length=Household._meta.get_field("invite_code").max_length,
        required=False,
        label="Invite code",
    )

    def clean(self):
        cleaned = super().clean()
        mode = cleaned.get("mode")
        if mode == "create":
            if not (cleaned.get("household_name") or "").strip():
                self.add_error(
                    "household_name", "Enter a name for your new household."
                )
        elif mode == "join":
            code = (cleaned.get("invite_code") or "").strip().upper()
            if not code:
                self.add_error("invite_code", "Enter an invite code.")
            else:
                try:
                    cleaned["household"] = Household.objects.get(invite_code=code)
                except Household.DoesNotExist:
                    self.add_error("invite_code", "Enter a valid invite code.")
        return cleaned

    def attach_household(self, user) -> Household:
        """Create the household (or use the joined one) and link the user to it."""
        if self.cleaned_data["mode"] == "create":
            household = Household.objects.create(
                name=self.cleaned_data["household_name"].strip()
            )
        else:
            household = self.cleaned_data["household"]
        Membership.objects.create(
            user=user, household=household, display_name=user.get_username()
        )
        return household


class RegisterForm(HouseholdChoiceForm, UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("username",)

    def save(self, commit=True):
        user = super().save(commit=commit)
        self.attach_household(user)
        return user


class ChoreForm(forms.ModelForm):
    class Meta:
        model = Chore
        fields = ["title", "description", "points", "is_active"]


class AssignmentForm(forms.ModelForm):
    class Meta:
        model = Assignment
        fields = ["assignee", "due_date"]
        widgets = {"due_date": forms.DateInput(attrs={"type": "date"})}

    def __init__(self, *args, household: Household, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["assignee"].queryset = household.members
        self.fields["assignee"].label_from_instance = lambda u: u.get_username()
