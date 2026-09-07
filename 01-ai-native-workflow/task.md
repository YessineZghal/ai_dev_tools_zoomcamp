# Choreo Implementation Plan (`task.md`)

> **Status: ✅ complete.** All 8 tasks implemented; `uv run python manage.py test`
> → 60 passing. Tasks 0–5 were committed locally as they were built; from Task 6
> on, changes were left uncommitted at the repo owner's request (handle git
> yourself). Feature views (Tasks 3–6) were wired in Task 2 because the shared
> nav template references their URL names — each feature's tests were still
> written and run in its own task.

> **For agentic workers:** Implement this plan task-by-task. Steps use checkbox
> (`- [ ]`) syntax for tracking. Check a box only after the step's command has
> run and produced the expected result.

**Goal:** Build **Choreo**, a Django app where one household manages shared
chores — catalogue, assign with due dates, complete with a permanent log, and a
dashboard of pending / overdue / leaderboard.

**Architecture:** One Django project `household`, one app `chores`, SQLite,
`uv`-managed env. Server-rendered templates + one CSS file, no JS, no API.
Django's built-in auth plus a custom `register` view that creates or joins a
`Household`. Every view scopes its queryset to the logged-in user's household.

**Tech Stack:** Python 3.12, Django 5.x, SQLite, `uv`, Django `TestCase`.

**Spec:** [`_docs/spec.md`](./_docs/spec.md) (plan: [`_docs/plan.md`](./_docs/plan.md))

## Global Constraints

- All work happens inside `01-ai-native-workflow/`. Paths below are relative to
  that directory. The Django project root (with `manage.py`) **is**
  `01-ai-native-workflow/`.
- Python `>=3.12`. Django: latest `5.x` resolved by `uv` at install time —
  record the exact version in `README.md`.
- Run every Python / Django command through `uv run` (e.g.
  `uv run python manage.py ...`).
- The Django app is named `chores`; it is registered in
  `household/settings.py` → `INSTALLED_APPS` as `"chores"`.
- No third-party packages beyond Django. No JavaScript. No CSS framework.
- Every queryset in a view is filtered to `request.user`'s household. New views
  without that filter are a bug.
- TDD: write the failing test first, watch it fail, implement, watch it pass,
  commit. One behaviour per test. Commit after every task.
- Commit message style: `feat: …`, `test: …`, `chore: …`, `docs: …`.
  End every commit body with:
  `Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>` and
  `Claude-Session: https://claude.ai/code/session_01TVaeNXBgQN6v6FzLHo5X2W`

---

## Task 0: Scaffold the uv project and Django

**Files:**
- Create: `pyproject.toml` (via `uv init`), `.python-version`
- Create: `manage.py`, `household/` (`__init__.py`, `settings.py`, `urls.py`,
  `wsgi.py`, `asgi.py`) via `django-admin startproject`
- Create: `chores/` app skeleton via `manage.py startapp`
- Modify: `household/settings.py` (register app, templates dir, login URLs)
- Create: `.gitignore`

**Interfaces:**
- Produces: a runnable Django project; `chores` app importable; `INSTALLED_APPS`
  contains `"chores"`.

- [x] **Step 1: Init the uv project**
  ```bash
  cd 01-ai-native-workflow
  uv init --name choreo --python 3.12 --no-workspace
  rm -f main.py hello.py        # remove uv's sample module if present
  ```
- [x] **Step 2: Add Django**
  ```bash
  uv add "django>=5,<6"
  uv run python -c "import django; print(django.get_version())"
  ```
  Expected: prints a `5.x` version.
- [x] **Step 3: Create the Django project in-place**
  ```bash
  uv run django-admin startproject household .
  ```
  Expected: `manage.py` and `household/` appear next to `pyproject.toml`.
- [x] **Step 4: Create the app**
  ```bash
  uv run python manage.py startapp chores
  ```
- [x] **Step 5: Register the app + config in `household/settings.py`**
  - Add `"chores"` to `INSTALLED_APPS`.
  - `TEMPLATES[0]["DIRS"] = [BASE_DIR / "templates"]`.
  - At the end of the file add:
    ```python
    LOGIN_URL = "login"
    LOGIN_REDIRECT_URL = "dashboard"
    LOGOUT_REDIRECT_URL = "login"
    ```
- [x] **Step 6: Write `.gitignore`** (Python + Django):
  ```gitignore
  __pycache__/
  *.py[cod]
  .venv/
  db.sqlite3
  *.log
  .DS_Store
  /staticfiles/
  .pytest_cache/
  ```
- [x] **Step 7: Verify the project boots**
  ```bash
  uv run python manage.py check
  uv run python manage.py migrate
  ```
  Expected: `check` → "System check identified no issues"; `migrate` applies
  Django's built-in migrations.
- [x] **Step 8: Commit**
  ```bash
  git add 01-ai-native-workflow
  git commit -m "chore: scaffold uv + Django project and chores app"
  ```

---

## Task 1: Domain models + admin + base template

**Files:**
- Modify: `chores/models.py`
- Create: `chores/tests/__init__.py`, `chores/tests/test_models.py`
- Modify: `chores/admin.py`
- Delete: `chores/tests.py` (replaced by the `tests/` package)
- Create: `templates/base.html`, `chores/static/chores/style.css`
- Create: `chores/migrations/0001_initial.py` (generated)

**Interfaces:**
- Produces:
  - `Household(name: str)` with auto field `invite_code: str` (6 chars,
    unique), `created_at`. Property `members` → `User` queryset.
  - `Membership(user: OneToOne[User], household: FK[Household],
    display_name: str, joined_at)`.
  - `Chore(household: FK, title: str, description: str, points: int=1,
    is_active: bool=True, created_at)`; `__str__` → title.
  - `Assignment(chore: FK, assignee: FK[User], due_date: date,
    status: str, completed_at: datetime|None, created_at)`;
    `status` choices `Assignment.Status.PENDING|DONE|SKIPPED`;
    method `is_overdue(today=None) -> bool`;
    method `complete(user, note="") -> CompletionEvent`;
    method `skip() -> None`.
  - `CompletionEvent(assignment: FK, completed_by: FK[User],
    completed_at: auto, points_awarded: int, note: str)`.
  - `User.membership` reverse accessor; helper
    `household_of(user) -> Household | None`.

- [x] **Step 1: Write failing model tests** in `chores/tests/test_models.py`:
  ```python
  from datetime import date, timedelta
  from django.contrib.auth.models import User
  from django.test import TestCase
  from chores.models import (
      Household, Membership, Chore, Assignment, CompletionEvent, household_of,
  )

  class HouseholdModelTests(TestCase):
      def test_invite_code_generated_and_unique(self):
          h1 = Household.objects.create(name="Flat A")
          h2 = Household.objects.create(name="Flat B")
          self.assertEqual(len(h1.invite_code), 6)
          self.assertTrue(h1.invite_code.isalnum())
          self.assertNotEqual(h1.invite_code, h2.invite_code)

      def test_members_and_household_of(self):
          h = Household.objects.create(name="Flat A")
          u = User.objects.create_user("ana", password="x")
          Membership.objects.create(user=u, household=h, display_name="Ana")
          self.assertIn(u, list(h.members))
          self.assertEqual(household_of(u), h)

      def test_household_of_returns_none_without_membership(self):
          u = User.objects.create_user("no_home", password="x")
          self.assertIsNone(household_of(u))

  class AssignmentModelTests(TestCase):
      def setUp(self):
          self.h = Household.objects.create(name="Flat A")
          self.u = User.objects.create_user("ana", password="x")
          Membership.objects.create(user=self.u, household=self.h, display_name="Ana")
          self.chore = Chore.objects.create(household=self.h, title="Dishes", points=3)

      def test_is_overdue_true_when_pending_and_past(self):
          a = Assignment.objects.create(
              chore=self.chore, assignee=self.u,
              due_date=date.today() - timedelta(days=1),
          )
          self.assertTrue(a.is_overdue())

      def test_is_overdue_false_when_done(self):
          a = Assignment.objects.create(
              chore=self.chore, assignee=self.u,
              due_date=date.today() - timedelta(days=1),
              status=Assignment.Status.DONE,
          )
          self.assertFalse(a.is_overdue())

      def test_complete_creates_event_and_sets_status(self):
          a = Assignment.objects.create(
              chore=self.chore, assignee=self.u, due_date=date.today(),
          )
          event = a.complete(self.u, note="sparkling")
          a.refresh_from_db()
          self.assertEqual(a.status, Assignment.Status.DONE)
          self.assertIsNotNone(a.completed_at)
          self.assertEqual(event.points_awarded, 3)
          self.assertEqual(event.completed_by, self.u)
          self.assertEqual(CompletionEvent.objects.count(), 1)

      def test_skip_sets_status_and_no_event(self):
          a = Assignment.objects.create(
              chore=self.chore, assignee=self.u, due_date=date.today(),
          )
          a.skip()
          a.refresh_from_db()
          self.assertEqual(a.status, Assignment.Status.SKIPPED)
          self.assertEqual(CompletionEvent.objects.count(), 0)
  ```
- [x] **Step 2: Delete `chores/tests.py`**, create `chores/tests/__init__.py`
  (empty). Run the tests to confirm they fail:
  ```bash
  uv run python manage.py test chores
  ```
  Expected: `ImportError` / `cannot import name` — models not defined yet.
- [x] **Step 3: Implement `chores/models.py`.** Key points:
  - `INVITE_ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"` (no ambiguous chars).
  - `Household.save()` generates a unique `invite_code` when blank (loop with
    `random.choices`, check `Household.objects.filter(invite_code=…).exists()`).
  - `members` property: `User.objects.filter(membership__household=self)`.
  - Module function `household_of(user)`:
    `getattr(getattr(user, "membership", None), "household", None)`.
  - `Assignment.Status` = `models.TextChoices` with `PENDING`, `DONE`, `SKIPPED`.
  - `is_overdue(today=None)`: `today = today or date.today();
    return self.status == self.Status.PENDING and self.due_date < today`.
  - `complete(user, note="")`: set `status=DONE`,
    `completed_at=timezone.now()`, `save()`, then create and return
    `CompletionEvent(assignment=self, completed_by=user,
    points_awarded=self.chore.points, note=note)`.
  - `skip()`: set `status=SKIPPED`, `completed_at=timezone.now()`, `save()`.
  - Sensible `Meta.ordering` and `__str__` on each model.
- [x] **Step 4: Make and run migrations**
  ```bash
  uv run python manage.py makemigrations chores
  uv run python manage.py migrate
  ```
- [x] **Step 5: Run the model tests**
  ```bash
  uv run python manage.py test chores.tests.test_models
  ```
  Expected: all pass.
- [x] **Step 6: Register all five models in `chores/admin.py`** with
  `@admin.register(...)` and a `list_display` for each.
- [x] **Step 7: Create `templates/base.html`** — `<!doctype html>`, `<head>`
  links `{% load static %}` → `chores/style.css`, a `<nav>` with links to
  `dashboard`, `chore_list`, `history`, a logout `<form method="post">`, and the
  current `user`. `{% block content %}{% endblock %}`. Wrap nav links in
  `{% if user.is_authenticated %}`.
- [x] **Step 8: Create `chores/static/chores/style.css`** — a small, clean
  stylesheet (system font stack, max-width container, card style for panels,
  a `.overdue` class in a warning colour, simple table styling). Keep it under
  ~120 lines.
- [x] **Step 9: `manage.py check` then commit**
  ```bash
  uv run python manage.py check
  git add 01-ai-native-workflow
  git commit -m "feat: add chore domain models, admin, and base template"
  ```

---

## Task 2: Authentication & household onboarding

**Files:**
- Create: `chores/forms.py`
- Modify: `chores/views.py`, `household/urls.py`
- Create: `chores/urls.py`
- Create: `templates/registration/login.html`,
  `templates/registration/register.html`,
  `templates/chores/household_setup.html`
- Create: `chores/tests/test_auth.py`

**Interfaces:**
- Consumes: `Household`, `Membership`, `household_of` from Task 1.
- Produces:
  - URL names: `login`, `logout` (Django built-ins), `register`,
    `household_setup`, `dashboard` (stub returning `render(base)` for now — real
    dashboard in Task 6).
  - `RegisterForm(UserCreationForm)` with extra fields:
    `mode` (`ChoiceField`: `create` / `join`), `household_name` (optional),
    `invite_code` (optional); `clean()` enforces the right field for the mode;
    `save()` creates the `User`, the `Household` (mode=create) or looks it up by
    code (mode=join), and the `Membership`.
  - `chores/forms.py::RegisterForm`, `chores/views.py::register`,
    `chores/views.py::household_setup`, `chores/views.py::dashboard`.

- [x] **Step 1: Write `chores/tests/test_auth.py`** covering:
  - `test_register_create_household`: POST to `register` with
    `mode=create, household_name="Flat A"` → 302 to `/`; `User` exists,
    `Membership` links to a `Household` named "Flat A", user is logged in.
  - `test_register_join_household`: pre-create a household; POST with
    `mode=join, invite_code=<code>` → user joins that household.
  - `test_register_join_bad_code`: `mode=join, invite_code="ZZZZZZ"` → form
    error, no user created.
  - `test_login_required_redirect`: GET `/` while anonymous → redirects to
    `/accounts/login/?next=/`.
  - `test_logout`: logged-in user POSTs to `logout` → redirected, session
    anonymous.
- [x] **Step 2: Run → fail**
  `uv run python manage.py test chores.tests.test_auth` (expected: 404/reverse
  errors — URLs not wired).
- [x] **Step 3: Implement `RegisterForm`** in `chores/forms.py`.
- [x] **Step 4: Implement `register`, `household_setup`, `dashboard` (stub)** in
  `chores/views.py`. `register`: on valid form, `form.save()`, then
  `login(request, user)`, redirect `dashboard`. `dashboard`:
  `@login_required`; if `household_of(request.user) is None` → redirect
  `household_setup`; else `render(request, "chores/dashboard.html", ctx)` — for
  this task a minimal context/template is fine (real one in Task 6).
- [x] **Step 5: Create `chores/urls.py`** with `app_name` omitted (use plain
  names) and wire `register`, `household_setup`, `dashboard`.
- [x] **Step 6: Update `household/urls.py`**:
  ```python
  from django.contrib import admin
  from django.urls import include, path

  urlpatterns = [
      path("admin/", admin.site.urls),
      path("accounts/", include("django.contrib.auth.urls")),
      path("accounts/register/", __import__("chores.views", fromlist=["register"]).register, name="register"),
      path("", include("chores.urls")),
  ]
  ```
  (Or cleaner: `from chores import views as chore_views` then
  `path("accounts/register/", chore_views.register, name="register")`.)
- [x] **Step 7: Templates** — `login.html` and `register.html` extend
  `base.html`, render the form with `{{ form.as_p }}` and a submit button;
  `household_setup.html` similar.
- [x] **Step 8: Run tests → pass**
  `uv run python manage.py test chores.tests.test_auth`
- [x] **Step 9: Manual smoke + commit**
  ```bash
  uv run python manage.py test chores
  git add 01-ai-native-workflow
  git commit -m "feat: register/login/logout with create-or-join household"
  ```

---

## Task 3: Chores CRUD (Feature 1)

**Files:**
- Modify: `chores/views.py`, `chores/urls.py`, `chores/forms.py`
- Create: `templates/chores/chore_list.html`,
  `templates/chores/chore_form.html`,
  `templates/chores/chore_confirm_delete.html`
- Create: `chores/tests/test_chores.py`

**Interfaces:**
- Consumes: `Chore`, `household_of`, `login_required`.
- Produces: URL names `chore_list`, `chore_create`, `chore_update`,
  `chore_delete`. `ChoreForm(ModelForm)` on
  `fields = ["title", "description", "points", "is_active"]`. All views
  `@login_required` and filter `Chore.objects.filter(household=household_of(user))`.

- [x] **Step 1: Write `chores/tests/test_chores.py`**:
  - `test_list_shows_only_my_household`: two households with a chore each; user
    in household A sees A's chore, not B's (asserts on response content).
  - `test_create_chore_attaches_household`: POST valid data → `Chore` created
    with `household == household_of(user)`, `points` respected.
  - `test_update_chore`: POST edit → fields change.
  - `test_delete_chore`: POST to delete → `Chore` gone, its assignments gone.
  - `test_cannot_edit_other_household_chore`: user A POSTs to edit B's chore →
    404.
- [x] **Step 2: Run → fail.**
- [x] **Step 3: Implement `ChoreForm` + the four views.** Use function-based
  views for consistency, or `ListView`/`CreateView`/`UpdateView`/`DeleteView`
  with `get_queryset` scoped to the household and `form_valid` setting
  `form.instance.household`. Either is fine — pick one and be consistent.
- [x] **Step 4: Add URLs** under `/chores/…` per `spec.md §7`.
- [x] **Step 5: Templates** — `chore_list.html` (table: title, points, active,
  open-assignments count, edit/delete/assign links, "New chore" button);
  `chore_form.html` (shared create/edit); `chore_confirm_delete.html`.
- [x] **Step 6: Run tests → pass; full suite → pass.**
  ```bash
  uv run python manage.py test chores
  ```
- [x] **Step 7: Run the dev server once and click through**
  ```bash
  uv run python manage.py runserver
  ```
  Visit `/chores/`, create/edit/delete a chore. Ctrl-C to stop.
- [x] **Step 8: Commit**
  `git commit -m "feat: household-scoped chores CRUD"`

---

## Task 4: Assignments — assign / complete / skip (Feature 2)

**Files:**
- Modify: `chores/views.py`, `chores/urls.py`, `chores/forms.py`
- Create: `templates/chores/assignment_form.html`
- Modify: `templates/chores/chore_list.html` (per-chore "Assign" + open
  assignments list)
- Create: `chores/tests/test_assignments.py`

**Interfaces:**
- Consumes: `Assignment`, `Chore`, `Assignment.complete`, `Assignment.skip`,
  `household_of`.
- Produces: URL names `assignment_create`, `assignment_complete`,
  `assignment_skip`. `AssignmentForm(ModelForm)` with
  `fields = ["assignee", "due_date"]`; `__init__` takes `household` and limits
  `assignee` queryset to `household.members`; `due_date` widget
  `type="date"`. `complete`/`skip` views are **POST-only**
  (`require_POST`), 404 if the assignment's chore isn't in the user's
  household.

- [x] **Step 1: Write `chores/tests/test_assignments.py`**:
  - `test_assign_limits_assignee_to_household`: form for household A does not
    accept a user from household B (`assertFormError` / 200 with error).
  - `test_assign_creates_pending_assignment`: POST → `Assignment` with
    `status=PENDING`, correct `chore`, `assignee`, `due_date`.
  - `test_complete_assignment_via_view`: POST to `assignment_complete` →
    `status=DONE`, one `CompletionEvent` with `points_awarded == chore.points`,
    `completed_by == request.user`.
  - `test_skip_assignment_via_view`: POST → `status=SKIPPED`, no event.
  - `test_complete_get_not_allowed`: GET → 405.
  - `test_cannot_complete_other_household_assignment`: 404.
- [x] **Step 2: Run → fail.**
- [x] **Step 3: Implement `AssignmentForm` + views** (`assignment_create` is a
  view on `chore_pk`; `assignment_complete` / `assignment_skip` are
  `@require_POST` and call the model methods, then redirect back to
  `next` or `dashboard`).
- [x] **Step 4: Add URLs.**
- [x] **Step 5: Templates** — `assignment_form.html`; update `chore_list.html`
  to show each chore's open assignments with Complete / Skip buttons
  (`<form method="post">` + `{% csrf_token %}`).
- [x] **Step 6: Run tests → pass; full suite → pass.**
- [x] **Step 7: Commit** `git commit -m "feat: assign, complete, and skip chore assignments"`

---

## Task 5: Completion log / history (Feature 3)

**Files:**
- Modify: `chores/views.py`, `chores/urls.py`
- Create: `templates/chores/history.html`
- Create: `chores/tests/test_history.py`

**Interfaces:**
- Consumes: `CompletionEvent`, `household_of`, `Membership`.
- Produces: URL name `history`. View `history` (`@login_required`):
  `events = CompletionEvent.objects.filter(
      assignment__chore__household=household_of(user)
  ).select_related("assignment__chore", "completed_by").order_by("-completed_at")`;
  optional `?member=<user_id>` filter; context also has `members` for the
  filter dropdown.

- [x] **Step 1: Write `chores/tests/test_history.py`**:
  - `test_history_lists_household_events_newest_first`.
  - `test_history_excludes_other_household`.
  - `test_history_member_filter`: `?member=<id>` returns only that member's
    events.
- [x] **Step 2: Run → fail.**
- [x] **Step 3: Implement the `history` view + URL.**
- [x] **Step 4: `history.html`** — member `<select>` (GET form) + a table
  (chore, who, when, points, note).
- [x] **Step 5: Run tests → pass; full suite → pass.**
- [x] **Step 6: Commit** `git commit -m "feat: completion history with member filter"`

---

## Task 6: Dashboard (Feature 4)

**Files:**
- Modify: `chores/views.py`
- Create/replace: `templates/chores/dashboard.html`
- Create: `chores/tests/test_dashboard.py`

**Interfaces:**
- Consumes: `Assignment`, `CompletionEvent`, `household_of`, `Membership`.
- Produces: real `dashboard` view context:
  - `my_pending`: `Assignment.objects.filter(assignee=user,
    status=PENDING).order_by("due_date")` with `is_overdue` available per row.
  - `household_overdue`: pending assignments in the household with
    `due_date < today`.
  - `recent_activity`: last 10 `CompletionEvent` for the household.
  - `leaderboard`: list of `{member, points}` = sum of `points_awarded` per
    `completed_by` over the last 30 days, ranked desc (include members with 0).
  - `invite_code`: `household_of(user).invite_code`.

- [x] **Step 1: Write `chores/tests/test_dashboard.py`**:
  - `test_dashboard_my_pending_only_mine_and_pending`.
  - `test_dashboard_overdue_panel`.
  - `test_dashboard_recent_activity_limit_10_and_scoped`.
  - `test_leaderboard_sums_last_30_days_points_desc`: create events with
    `completed_at` inside and outside 30 days (use
    `CompletionEvent.objects.filter(...).update(completed_at=…)` to backdate);
    assert ordering and that the old one is excluded.
  - `test_dashboard_shows_invite_code`.
- [x] **Step 2: Run → fail** (dashboard is still the stub).
- [x] **Step 3: Implement the real `dashboard` view.** Leaderboard query:
  ```python
  from django.db.models import Sum
  from django.utils import timezone
  since = timezone.now() - timezone.timedelta(days=30)
  rows = (
      CompletionEvent.objects
      .filter(assignment__chore__household=hh, completed_at__gte=since)
      .values("completed_by")
      .annotate(points=Sum("points_awarded"))
  )
  ```
  Merge with `hh.members` so zero-score members still appear; sort by points
  desc then display name.
- [x] **Step 4: Build `dashboard.html`** — four `<section class="card">`
  panels + the invite code. Use the `.overdue` CSS class on overdue rows.
- [x] **Step 5: Run tests → pass; full suite → pass.**
- [x] **Step 6: Manual click-through of the whole flow**
  (register → household → chore → assign → complete → dashboard + history).
- [x] **Step 7: Commit** `git commit -m "feat: dashboard with pending, overdue, activity, leaderboard"`

---

## Task 7: Test suite review & coverage pass

**Files:**
- Modify: any `chores/tests/test_*.py` with gaps
- Create: `chores/tests/test_isolation.py` (cross-cutting data-isolation tests)

- [x] **Step 1: List the scenarios** the suite must cover and check each has a
  test (write to the "Testing" section of `README.md`):
  1. Model: invite code generation & uniqueness.
  2. Model: `is_overdue` true/false paths.
  3. Model: `complete()` creates an event with the right points; `skip()`
     doesn't.
  4. Auth: register → create household; register → join by code; bad code
     rejected.
  5. Auth: login required on protected views; logout works.
  6. **Isolation:** household A cannot list, view, edit, delete, assign, or
     complete household B's chores/assignments (dedicated test file).
  7. Chores: CRUD happy paths; cascade delete removes assignments.
  8. Assignments: assignee limited to household; create → PENDING;
     complete → DONE + event; skip → SKIPPED; POST-only enforced.
  9. History: newest-first, household-scoped, member filter.
  10. Dashboard: each panel's contents and scoping; leaderboard 30-day window
      and ordering; invite code shown.
- [x] **Step 2: Add `chores/tests/test_isolation.py`** consolidating the
  cross-household negative cases (some may duplicate earlier tests — that's
  fine, this file is the single place a reviewer checks isolation).
- [x] **Step 3: Run the full suite verbosely**
  ```bash
  uv run python manage.py test -v 2
  ```
  Expected: all green. Fix any failures before continuing.
- [x] **Step 4: Check for obvious gaps** with a coverage eyeball (optional):
  ```bash
  uv run python -m pip install coverage >/dev/null 2>&1 || true
  ```
  (Skip if `coverage` isn't trivially available — not a dependency.)
- [x] **Step 5: Commit** `git commit -m "test: consolidate data-isolation tests and coverage pass"`

---

## Task 8: README, docs, and push

**Files:**
- Create: `README.md`
- Modify: `_docs/plan.md`, `backlog.md` (tick completed items)
- Create: `backlog.md` if not already created in a checkpoint

- [x] **Step 1: Write `backlog.md`** — the numbered Django backlog derived from
  this plan (Task 0–8 → backlog items 1–N with one-line descriptions and
  acceptance criteria). Homework Q4 answer = backlog item 1.
- [x] **Step 2: Write `README.md`** — see the "README contents" section below.
- [x] **Step 3: Fill in the 6 homework answers** in `README.md`:
  - Q1: Claude Code.
  - Q2: the 4 features (Chores CRUD, Assignments, Completion log, Dashboard).
  - Q3: `settings.py`.
  - Q4: backlog item 1's title.
  - Q5: `uv run python manage.py runserver`.
  - Q6: `uv run python manage.py test`.
- [x] **Step 4: Final full verification**
  ```bash
  uv run python manage.py check
  uv run python manage.py makemigrations --check --dry-run
  uv run python manage.py test
  ```
  All must pass / report no changes.
- [x] **Step 5: Commit and push**
  ```bash
  git add 01-ai-native-workflow
  git commit -m "docs: README, backlog, and homework answers for HW1"
  git push origin main
  ```

---

## README contents (Task 8, Step 2)

The `README.md` must include, in this order:

1. **Title + one-line description** of Choreo.
2. **The homework** — link to `homework.md`, one sentence on the AI-native
   workflow used (idea → spec → plan → backlog → implement → test).
3. **Features** — the 4, one paragraph each, mapped to spec `F1–F4`.
4. **Screenshots or a short screen-by-screen walkthrough** (text is fine).
5. **Tech stack** — Python 3.12, exact Django version, SQLite, uv.
6. **Getting started**:
   ```bash
   cd 01-ai-native-workflow
   uv sync
   uv run python manage.py migrate
   uv run python manage.py createsuperuser   # optional, for /admin
   uv run python manage.py runserver
   ```
   Then open http://127.0.0.1:8000/ and register.
7. **Running the tests** — `uv run python manage.py test`, plus the list of
   scenarios covered (from Task 7 Step 1).
8. **Project layout** — annotated tree.
9. **Data model** — the table from the spec (or a small diagram).
10. **AI-native workflow notes** — how the spec/plan/backlog docs were produced
    and how tasks were implemented one at a time.
11. **Homework answers** — a table with Q1–Q6 and the chosen answers.
12. **What's next / out of scope** — recurring chores, notifications, API.

---

## Self-review (done before execution)

- **Spec coverage:** F1→Task 3, F2→Task 4, F3→Task 5, F4→Task 6, auth §5→Task 2,
  data model §6→Task 1, URLs §7→Tasks 2–6, UI §8→Task 1 (base) + per-feature
  templates, success criteria §11→Tasks 7–8. No gaps.
- **Placeholders:** none — every task names exact files, URL names, model
  members, and commands; test scenarios are concrete.
- **Type consistency:** `household_of(user)`, `Assignment.Status`,
  `Assignment.is_overdue()`, `Assignment.complete(user, note="")`,
  `Assignment.skip()`, `CompletionEvent.points_awarded` are used with the same
  names/signatures in every task that references them.
