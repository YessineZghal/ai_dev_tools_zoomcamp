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
| 10 | v2-A: review fixes (notes UI, chore_list prefetch) | done |
| 11 | v2-B: recurring chores (+ rotation, + `generate_recurring`) | done |
| 12 | v2-C: household / members page | done |
| 13 | v2-D: My Chores page + nav overdue badge | done |
| 14 | v2-E: docs refresh | done |

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

---

## v2 — Review fixes + feature additions

Full detail in [`task-v2.md`](./task-v2.md).

### Task 10 — Review fixes
Completion notes reachable from the UI (dedicated `GET` form on
`assignment_complete`); `chore_list` prefetches only pending assignments.

### Task 11 — Recurring chores
`Chore.recurrence` + `rotate_assignee`; `Assignment.spawn_next()` on
complete/skip; `manage.py generate_recurring` safety-net command.
**Acceptance:** `test_recurring.py` green (15 tests).

### Task 12 — Household / members page
`/household/` roster with 30-day points + pending counts, invite code, editable
own display name (now shown on the leaderboard).

### Task 13 — My Chores page + nav badge
`/mine/` with a status filter; `overdue_badge` context processor drives a red
nav badge.

### Task 14 — Docs refresh
README v2 section, `_docs/spec.md` §9/§12 update, screenshots, test counts.
