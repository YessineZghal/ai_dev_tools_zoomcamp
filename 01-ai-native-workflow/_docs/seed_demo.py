"""Populate the database with a demo household.

Run with:  uv run python manage.py shell < _docs/seed_demo.py

Creates the household "Maple Street 12" with members ana / ben / cleo
(password: demo-pass-123), four chores, open + overdue assignments, and
some completion history. Safe to re-run: it clears non-superuser users and
all households first.
"""

from datetime import date, timedelta

from django.contrib.auth.models import User

from chores.models import Assignment, Chore, Household, Membership

Household.objects.all().delete()
User.objects.filter(is_superuser=False).delete()

household = Household.objects.create(name="Maple Street 12")
ana = User.objects.create_user("ana", password="demo-pass-123")
ben = User.objects.create_user("ben", password="demo-pass-123")
cleo = User.objects.create_user("cleo", password="demo-pass-123")
for user in (ana, ben, cleo):
    Membership.objects.create(
        user=user, household=household, display_name=user.username
    )

dishes = Chore.objects.create(
    household=household, title="Wash the dishes", points=2,
    description="Including the pans.",
    recurrence=Chore.Recurrence.DAILY, rotate_assignee=True,
)
trash = Chore.objects.create(
    household=household, title="Take out the trash", points=1,
    recurrence=Chore.Recurrence.WEEKLY,
)
vacuum = Chore.objects.create(household=household, title="Vacuum living room", points=3)
bathroom = Chore.objects.create(
    household=household, title="Clean the bathroom", points=5,
    recurrence=Chore.Recurrence.MONTHLY,
)

ana.membership.display_name = "Ana"
ana.membership.save()
ben.membership.display_name = "Ben"
ben.membership.save()

today = date.today()
Assignment.objects.create(chore=dishes, assignee=ana, due_date=today)
Assignment.objects.create(chore=trash, assignee=ben, due_date=today - timedelta(days=2))
Assignment.objects.create(chore=vacuum, assignee=cleo, due_date=today + timedelta(days=1))
Assignment.objects.create(chore=bathroom, assignee=ana, due_date=today - timedelta(days=1))

for chore, who, days_ago in [
    (dishes, ben, 3),
    (vacuum, ana, 4),
    (trash, cleo, 1),
    (bathroom, ben, 6),
]:
    done = Assignment.objects.create(
        chore=chore, assignee=who, due_date=today - timedelta(days=days_ago)
    )
    done.complete(who)

print(f"Seeded household '{household.name}' (invite code {household.invite_code}).")
print("Log in as ana / ben / cleo with password 'demo-pass-123'.")
