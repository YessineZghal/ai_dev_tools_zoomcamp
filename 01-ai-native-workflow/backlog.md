# Choreo — Django Backlog

Derived from [`_docs/plan.md`](./_docs/plan.md) and
[`_docs/spec.md`](./_docs/spec.md). Each item is a self-contained slice that
ends with passing tests. Status reflects the current repo.

| # | Task | Status |
|---|------|--------|
| 1 | Project setup | done |
| 2 | Domain models + admin + base template | done |
| 3 | Authentication & household onboarding | done |
| 4 | Chores CRUD (Feature 1) | done |
| 5 | Assignments — assign / complete / skip (Feature 2) | done |
| 6 | Completion log / history (Feature 3) | done |
| 7 | Dashboard (Feature 4) | done |
| 8 | Test suite & data-isolation pass | done |
| 9 | Docs (README, backlog) | done |

---

## Task 1 — Project setup

Create the `uv` project, install Django 5.x, generate the `household` project
and the `chores` app, and **register `chores` in `household/settings.py`
(`INSTALLED_APPS`)**. Configure `TEMPLATES["DIRS"]`, the auth redirect URLs, and
add `.gitignore`.

**Acceptance:** `uv run python manage.py check` and
`uv run python manage.py migrate` succeed.

## Task 2 — Domain models + admin + base template

Add `Household`, `Membership`, `Chore`, `Assignment`, `CompletionEvent` with
invite-code generation, `Assignment.is_overdue()`, `Assignment.complete()` and
`Assignment.skip()`. Register all models in the admin. Create `base.html` and
the stylesheet.

**Acceptance:** model tests for invite codes, overdue logic, and completion
events pass; `makemigrations` produces one migration.

## Task 3 — Authentication & household onboarding

Django login/logout plus a custom `register` view whose form also creates a new
household or joins one by invite code. Add a `household_setup` fallback page.

**Acceptance:** register→create, register→join, bad-code rejection, and
login-required redirects are covered by tests.

## Task 4 — Chores CRUD (Feature 1)

List / create / update / delete chores, every query scoped to the current
user's household. `ChoreForm` on `title, description, points, is_active`.

**Acceptance:** list isolation, create attaches the right household, cascade
delete, and cross-household 404s pass.

## Task 5 — Assignments (Feature 2)

Assign a chore to a household member with a due date; complete (→ records a
`CompletionEvent`) and skip actions are POST-only. `AssignmentForm` limits the
assignee choices to household members.

**Acceptance:** assignee restriction, PENDING on create, event + points on
complete, no event on skip, 405 on GET, cross-household 404.

## Task 6 — Completion log / history (Feature 3)

`history` view lists the household's completion events newest-first with an
optional `?member=<id>` filter.

**Acceptance:** ordering, household scoping, and member filter pass.

## Task 7 — Dashboard (Feature 4)

Landing page with four panels — my pending chores, household overdue, recent
activity (last 10), 30-day points leaderboard — plus the invite code.

**Acceptance:** each panel's contents and scoping, leaderboard window and
ranking, zero-score members included, invite code shown.

## Task 8 — Test suite & data-isolation pass

Consolidate cross-household negative cases into `test_isolation.py`, add an
end-to-end `test_journey.py`, and switch to a fast password hasher under
`test`.

**Acceptance:** `uv run python manage.py test` is green.

## Task 9 — Docs

`README.md` with setup, feature descriptions, test list, project layout, and
the six homework answers; keep `backlog.md` and `_docs/plan.md` current.
