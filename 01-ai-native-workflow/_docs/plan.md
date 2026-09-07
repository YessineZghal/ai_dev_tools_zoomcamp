# Choreo — Plan

> The homework's `_docs/plan.md`. High-level plan derived from
> [`spec.md`](./spec.md). The granular, step-by-step coding checklist lives in
> [`../task.md`](../task.md); the ordered task list in
> [`../backlog.md`](../backlog.md).

## What we're building

**Choreo**, a Django web app for one household to manage shared chores:
catalogue chores, assign them with due dates, mark them done with a permanent
log, and see pending / overdue / leaderboard info on a dashboard.

## Features (spec)

1. **Chores CRUD** — manage the household's chore catalogue.
2. **Assignments** — assign a chore to a member with a due date; track
   pending / overdue.
3. **Completion log** — immutable history of completed chores, filterable by
   member.
4. **Dashboard** — my chores, household overdue, recent activity, 30-day
   points leaderboard, invite code.

## Architecture

- Single Django project **`household`**, single app **`chores`**.
- SQLite database (Django default), `uv`-managed environment.
- Server-rendered templates + one hand-written CSS file. No JS, no API.
- Django's built-in auth; one custom `register` view that also
  creates-or-joins a `Household`.
- Every view scopes its queryset to the logged-in user's household —
  data isolation is enforced in the views, tested explicitly.

## Data model

`Household` → has many `Membership` (one per `User`) → has many `Chore` →
has many `Assignment` → has many `CompletionEvent`. See `spec.md §6` for
fields.

## Build phases

| Phase | Deliverable | Homework tie-in |
|---|---|---|
| 0 | `uv` project, Django installed, `household` project + `chores` app created and **registered in `settings.py`** | Q3 |
| 1 | Models (`Household`, `Membership`, `Chore`, `Assignment`, `CompletionEvent`), migrations, admin, `base.html` + CSS | Q4 task 1 |
| 2 | Auth: login/logout, `register` (create-or-join household), `household_setup` | |
| 3 | Chores CRUD (F1) | Q5 (run server) |
| 4 | Assignments: assign / complete / skip, overdue logic (F2) | |
| 5 | Completion log page with member filter (F3) | |
| 6 | Dashboard with the four panels + leaderboard (F4) | |
| 7 | Test suite across all features | Q6 |
| 8 | `README.md`, `.gitignore`, docs polish, commit & push | GitHub repo section |

Each phase ends with a green test run and a git commit. TDD: write the test
for a behaviour before the code that satisfies it.

## Risks / decisions

- **Household join** adds a little logic (invite code, create-or-join form).
  Kept because "shared" is the point of the tool; mitigated by good tests.
- **Data isolation** is the main correctness risk in a multi-household app.
  Handled with a `household_scoped` helper on the manager/queryset and a
  dedicated test that one household cannot see another's chores.
- Django version: pin to the latest 5.x at install time; record the exact
  version in `README.md` and `pyproject.toml`.

## Out of scope

Recurring chores, notifications, REST API, multi-household users, deployment.
See `spec.md §9`.
