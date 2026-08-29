**A backend-only, JSON-response Django project applying everything from Phases A–O**

---

## 1. Overview

You're building the backend for a small Stack Overflow-style Q&A platform: users ask questions, other users answer them, questions can be tagged, answers can be voted on, and question authors can mark an answer as "accepted." No templates, no HTML pages — every endpoint returns JSON. This is deliberately a **new domain**, not your `blog` app, so you're applying the concepts independently rather than adapting existing code.

This project is scoped to what you've actually covered (Phases A–O). It does **not** require DRF, formal automated testing (`pytest`/`TestCase`), Docker, or deployment — those come later in your roadmap. Verification here is manual, via `curl` and the Django shell, exactly like your phase artifacts.

## 2. Data Model

Design and build these models yourself — field types, relationships, and constraints are your decisions, informed by everything in Phase F. Minimum required shape:

```
User (Django's built-in)
    ↓ OneToOne
UserProfile — reputation (int, default 0), bio (optional)

Question
    - title, body, created_at
    - author → ForeignKey to User
    - tags → ManyToManyField to Tag
    - accepted_answer → ForeignKey to Answer, nullable (careful: this creates a circular reference — think about how to handle it)

Answer
    - body, created_at
    - question → ForeignKey to Question
    - author → ForeignKey to User
    - is_accepted → BooleanField, default False

Tag
    - name, unique

Vote
    - user → ForeignKey to User
    - answer → ForeignKey to Answer
    - value → IntegerField, choices restricted to +1 / -1
    - a user should not be able to vote twice on the same answer (think about which Phase F, Artifact 3 tool enforces this at the database level)

Comment
    - body, created_at
    - question → ForeignKey to Question
    - author → ForeignKey to User
```

You'll need to think through the `Question.accepted_answer` circular reference problem yourself — this is a deliberate, realistic modeling challenge, not an oversight in these instructions.

## 3. Required Functionality

**Models & Migrations (Phase F, G)**

- All models above, with sensible `null`/`blank`/`choices`/`default` usage and a real migration history.
- At least one deliberate data migration (Phase G, Artifact 2) — for example, backfilling `UserProfile.reputation` for any users that predate the field.

**ORM (Phase H, I, J)**

- A `GET /questions/` endpoint listing questions with: tag names, author username, and answer count — built using `.annotate()` (Phase H, Artifact 3).
- This endpoint must **not** have an N+1 problem. Use `select_related`/`prefetch_related` (Phase J, Artifact 2) correctly, and verify your query count directly with `connection.queries` before considering this done.
- Voting must use `F()` expressions (Phase H, Artifact 3) to update `UserProfile.reputation` — never read-modify-write in Python.
- Accepting an answer (author-only) must happen inside a `transaction.atomic()` block (Phase J, Artifact 3): marking the answer accepted, unmarking any previously accepted answer, and updating the answerer's reputation must all succeed or fail together.

**Authentication & Authorization (Phase K)**

- Session-based login/logout/whoami endpoints (mirror Phase K, Artifact 2).
- Only authenticated users can post questions, answers, comments, or votes.
- Only a question's author can accept an answer to their own question — this is **object-level authorization** (Phase K, Artifact 4), not just "is logged in."
- Only an answer/comment's author (or staff) can delete it.

**Admin (Phase L)**

- Register every model with sensible `list_display`/`list_filter`/`search_fields`.
- `Answer` should be manageable inline under `Question` in the admin.
- At least one custom admin action (e.g., "mark selected questions as closed" — add a `is_closed` field if you go this route).

**Forms/Validation (Phase M)**

- Even though this is a JSON API, use `forms.Form` or `forms.ModelForm` server-side to validate incoming POST data (title length, body not empty, etc.) rather than hand-rolling `if` checks — this is a deliberate choice to reinforce Phase M, not a requirement to build HTML pages.

**Middleware & Signals (Phase N)**

- A custom middleware logging every request's method, path, and response time (mirror Phase N, Artifact 1).
- A signal that automatically creates a `UserProfile` when a new `User` is created (mirror Phase N, Artifact 2).
- A signal that updates `UserProfile.reputation` whenever a `Vote` is created or deleted (up +10 for an accepted answer is a reasonable rule to invent yourself — document whatever scoring rule you choose).

**Security (Phase O)**

- CSRF protection genuinely working (not blanket-exempted).
- `settings.py` using the environment-variable + `DEBUG`conditional security pattern from Phase O, Artifact 2.
- Run `python manage.py check --deploy` against your finished project and resolve every warning you reasonably can.

## 4. Required Endpoints (minimum set — you may add more)

```
POST   /login/
POST   /logout/
GET    /whoami/

GET    /questions/                 — list, with tags/author/answer_count, N+1-safe
POST   /questions/                 — create (auth required)
GET    /questions/<id>/            — detail, including answers and comments
POST   /questions/<id>/answers/    — post an answer (auth required)
POST   /answers/<id>/accept/       — accept an answer (author-only, atomic)
POST   /answers/<id>/vote/         — vote (auth required, one vote per user per answer)
POST   /questions/<id>/comments/   — post a comment (auth required)
DELETE /answers/<id>/              — delete (author or staff only)
```

## 5. Acceptance Checklist — Self-Verification

Work through this like a QA pass. Formal automated testing is a later phase in your roadmap (Phase 12), so this checklist is deliberately manual — `curl` and the Django shell, exactly like your artifacts.

**Functional correctness**

- [ ]  A logged-out user gets `401`/`403` (your choice, be consistent) attempting to post a question, answer, comment, or vote.
- [ ]  A logged-in user can create a question, tag it, and see it in `GET /questions/`.
- [ ]  A user who is NOT the question's author gets `403` attempting to accept an answer to it.
- [ ]  The question's actual author CAN accept an answer, and the previous accepted answer (if any) is correctly unmarked.
- [ ]  Voting twice on the same answer by the same user fails at the database level (an `IntegrityError`, not just app-level logic) — confirm this in the shell directly.
- [ ]  Deleting an answer as a non-author, non-staff user is rejected.

**ORM correctness (Phase H/I/J)**

- [ ]  Using `connection.queries` (Phase I, Artifact 1), confirm `GET /questions/` executes a small, fixed number of queries regardless of how many questions/tags/answers exist — no N+1.
- [ ]  Confirm reputation updates via voting use `F()`, not a Python read-modify-write — inspect the generated SQL to prove it.
- [ ]  Confirm accepting an answer is genuinely atomic: deliberately trigger a failure partway through (e.g., temporarily break the reputation update logic) and confirm the accepted-answer change also rolls back, not just partially applies.

**Security (Phase O)**

- [ ]  A POST request without a valid CSRF token is rejected with `403`.
- [ ]  `python manage.py check --deploy` run with `DEBUG=False` shows no unresolved warnings you can't justify.
- [ ]  `SECRET_KEY` and all environment-specific values are read from `.env`, not hardcoded (Phase A, Artifact 4).

**Admin (Phase L)**

- [ ]  Every model is visible and manageable in `/admin/`.
- [ ]  `Answer` can be added/edited inline from a `Question`'s admin page.
- [ ]  Your custom admin action works correctly on a multi-row selection.

**Code quality**

- [ ]  Every model has a meaningful `__str__`.
- [ ]  `Meta.ordering` is set sensibly on at least `Question` and `Answer`.
- [ ]  Your custom middleware and signals are genuinely connected (verify `AppConfig.ready()`) and firing — confirm via your terminal logs.

## 6. Stretch Goals (optional, not required to consider the project done)

- Add search/filtering to `GET /questions/` using the lookup vocabulary from Phase H, Artifact 2 (e.g., `?tag=django`, `?search=queryset`).
- Add a `Question.is_closed` field and prevent new answers on closed questions — a good object-level authorization exercise.
- Add rate-limiting middleware: reject a user's 6th question-post within a rolling 60-second window (a genuine, non-trivial middleware exercise beyond Phase N's examples).

## 7. What "done" looks like

You should be able to walk through every item in Section 5 and honestly check it off, using the same verification habits you built throughout Phases H, I, and J — inspecting real query counts, real generated SQL, and real HTTP responses, not just assuming the code is correct because it looks right.

When you're done, come back and I'm happy to review specific pieces, help debug something that's not behaving as expected, or talk through any modeling decisions you made differently than suggested here (like how you resolved the `accepted_answer` circular reference).

The core idea