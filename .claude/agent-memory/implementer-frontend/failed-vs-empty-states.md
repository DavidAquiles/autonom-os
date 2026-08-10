---
name: failed-vs-empty-states
description: A request that FAILED must never render as data that is EMPTY or GONE — the app has one shared ListFailure state; extend it rather than inventing a second
metadata:
  type: project
---

In this app an error state must never make a factual claim about the data, and
the not-found state must **replace** a record rather than render above it.
`routes/finanzas/ListFailure.tsx` is the single shared "this list did not load"
banner (violet, with **Reintentar**). Extend it; do not add a second error state.

**Why:** QA rework cycle 1 (Run 02) found three defects of one shape. A failed
category-list request rendered 18.10's *"En agosto ya no queda nada en Transporte"*
while the breakdown above still showed Transporte's total — the screen
contradicted itself and the false half was the reassuring one. Historial rendered
a completely empty `<main>` on the same failure. And a deleted expense's detail
rendered the whole record *underneath* "Este gasto ya no existe.", with a live
edit button whose save then blamed a server that was answering.

The mechanism behind all three: **TanStack keeps the last good `data` when a
refetch fails**, so `data` and `error` are both truthy, and a branch written as
`data ? rows : emptyState` silently catches every failure.

**How to apply:**
- Gate an empty-state claim on `query.isSuccess`, never on `!isPending` or on a
  falsy `data`. That single word is the difference between "there is nothing
  here" and "I do not know what is here".
- Gate a record's render on `!missing` (the `not_found` `ApiError`), and drop its
  actions with it. Cached data under a *reachability* banner is fine and is what
  the mockups draw — out of date is worth reading, gone is not.
- `ListFailure` returns `null` when `useHealth()` is errored, because
  `ReachabilityBanner` (App.tsx) is already saying that. Two banners about one
  condition, in two wordings, is the same self-contradicting screen. Decide
  "unreachable" from **health**, not from the error's class: a request blocked at
  the network layer raises `UnreachableError` for a server that is answering.
- Red stays out: `estilos.test.ts` allowlists `var(--danger…)` to three files,
  and a list that did not load is not a failed write.

Related: [[verify-interactive-states]], [[autonomos-context]].
