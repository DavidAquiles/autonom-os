---
name: factory-lane-discipline
description: Stage only your own lane's paths in this repo; another agent is editing the same working tree at the same time
metadata:
  type: feedback
---

Never run `git add -A`, `git add .` or `git commit -a` in this repository. Stage
the paths the current lane owns, explicitly — for the backend lane that is
`backend/ ops/ factory/implementer-backend/`.

**Why:** the factory runs `implementer-backend` and `implementer-frontend`
concurrently in one working tree. In an earlier pilot an `add -A` swept 34 of
another role's in-flight files into a commit whose message described something
else; nothing was lost, but the history lied. Files under `frontend/` and
`mockups/` are the other lane's and must not be read, edited, reverted or stashed.

**How to apply:** stage explicitly, run `git status --porcelain` before committing
and confirm nothing outside the lane is staged, and name the lane in the commit
subject (`backend: ...`). Also expect the other lane's processes on the host — a
mock API held port 8000 during the 2026-08-05 implement stage; work around it
rather than killing it.

Related: [[project-autonomos]]
