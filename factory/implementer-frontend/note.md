# Frontend implementation note (Phase 2)

## Summary

`frontend/` is a React 18 + TypeScript + Vite SPA (~6,700 lines across 59 source
files) built to `frontend/dist` and served by the backend from one origin. It
covers all six routes in Architect's list, the seven form/reader sub-routes they
imply, and voice capture end to end. Styling is `styles/tokens.css` plus CSS
Modules per component, exactly as KD-14 requires; the whole palette is in one
36-line token block carried unchanged from the approved mockups.

Three things downstream needs to know before reading further:

1. **`partial_answer` is gone from the waiting screen, as instructed.** The
   preview block is deleted; the tally, the seconds count, the honest-range copy
   and the cancel affordance are unchanged. `elapsed_ms` is the only progress
   signal the UI reads, and no `Tally` prop exists that could accept a total.
2. **Verification found three real defects and they are fixed.** Two CSS
   specificity bugs invisible in the mockups (the active nav item was not violet;
   the red error border lost to `:focus`) and one sub-44px touch target. All were
   caught by rendering and looking, not by reading.
3. **The offline screen no longer hardcodes `https://192.168.1.24:8443`.** KD-2
   forbids an origin or port in the bundle, and the built assets contain neither.
   The LAN address is remembered from the visit setup makes to that origin.

82 screenshots at 390/360/320/900 px, including forced `:hover`,
`:focus-visible`, `:active` and `disabled`, are in `frontend/tools/shots/`, with
`audit.json` beside them. 29 frontend tests pass. The build carries no origin, no
port and no external request.

## How to run it

```bash
cd frontend
npm install
npm run build          # tsc --noEmit && vite build → frontend/dist (+ dist/sw.js)
npm test               # 29 tests
npm run dev            # dev server on 5173, /api proxied to 127.0.0.1:8001
```

In production the backend serves `dist`:

```bash
cd backend
FRONTEND_DIST=../frontend/dist .venv/bin/python -m autonomos.serve
# http://127.0.0.1:8001/  — SPA and API on one origin
```

Verification tooling and how to re-run it: `frontend/tools/README.md`.

## Fidelity to the approved mockups

Every approved screen is built. Structure, type scale, spacing, tints and copy
are carried from `mockups/_build/` rather than re-derived. Departures, all
deliberate:

| Departure | Why |
|---|---|
| **The live-preview block is removed from the question wait** (`analisis-esperando`) | Instructed. `partial_answer` is not on the wire (KD-11); a figure shown then retracted was still shown. Everything else on that screen is unchanged. |
| **The offline screen shows no hardcoded LAN address** | KD-2: no origin or port in the bundle. `src/state/origin.ts` remembers the origin when the app is served from something other than the tailnet — which happens when setup installs the second home-screen icon. Before that there is no address to offer, and the screen says where the home version is instead of inventing one. `sin-servidor.png` shows the state with nothing remembered; the "Abrir la versión de casa" link appears once it is. **This is the one place the built UI cannot look like the approved mockup.** |
| **A "Preguntar" button appears under the ask row once it has text** | The approved ask row is an input plus a mic with no visible submit. On a phone that is only reachable via the keyboard's "Ir" key — and a *spoken* question arrives with no keyboard up, so it would be unsendable. The row itself is unchanged; the button only exists when the field is non-empty. See `analisis-preguntar.png`. |
| **The phone frame and simulated status bar are gone** | Mockup scaffolding, named as such in the Phase 1 note. |
| **`/finanzas/ajustes` splits into a list and a per-item editor** (`/finanzas/ajustes/:kind/:id`) | The mockups showed both screens; the route was implied but unnamed. |
| **The Diario "Por fecha" tab is a real route** (`/diario/fecha`) | The mockup reached it from the tab strip; it needed a URL. |

Two things the mockups showed as one screen are now two states of one component,
with no visual change: `gasto-nuevo` / `gasto-editar` / `gasto-voz-revision` are
one form, and `diario-escribir` / `diario-voz-revision` are one editor.

## Visual Direction Conformance

Each numbered Design Constraint, and how it was verified. "Audited" means
`tools/shots.mjs` measured it in the browser across all 82 captures, including
under forced pseudo-states; the run exits non-zero on any finding and currently
reports **0**.

| # | Status | How verified |
|---|---|---|
| 1 white dominant | Met | Every capture. The largest violet area in the app is the 132 px recording pulse, which is a transient full-attention state, not a page background. |
| 2 one brand hue | Met | `src/test/estilos.test.ts` fails the build on any literal colour outside `tokens.css` except `#fff`. |
| 3 one functional red | Met, **with one disclosure** | Same test pins `--danger` to three files: destructive buttons, validation errors, and the failed-save banner. **The failed-save banner is red and is not literally "destructive confirmation or validation error".** It is red in the approved mockup (`gasto-guardar-fallo`), and the Phase 1 note's constraint-3 list did not mention it because it was an inline style. Flagged for Reviewer rather than quietly changed. |
| 4 violet tints only | Met | `--t1…--t10`, one hue, asserted by test; `finanzas-mes.png`. |
| 5 WCAG AA | Met | Audited: every text node against its actually-painted background, 4.5:1 / 3:1, in default, hover, focus, active and disabled. 0 failures. |
| 6 no colour-only meaning | Met | Every breakdown row prints name, amount and percent beside the bar; payment rows print name and amount. |
| 7 390 px, no h-scroll, no zoom | Met | Audited at 390, 360 and 320 px: `scrollWidth > innerWidth` is false everywhere. Smallest text is 13.5 px; the only 11.5 px text is uppercase letterspaced labels. |
| 8 no desktop layout | Met | `width: min(390px, 100vw)` centred; `finanzas-hoy--900.png`, `diario--900.png`. |
| 9 thumb-zone capture | Met | The capture bar sits directly above the nav on every Finanzas and Diario screen: 52 px pill and 58 px circle in the bottom ~135 px. |
| 10 ≥44×44 targets | Met | Audited every interactive box in every state. **It caught one regression** — the LLM-unavailable banner link at 178×19 — fixed at `Analisis.tsx:103`. 0 remaining. |
| 11 three destinations everywhere | Met | The nav is part of `Screen`, not of any route, so it cannot be omitted. Present on the Gym placeholder, the offline screen and every voice state. Test asserts exactly three `<a>`. |
| 12 one family, aligned numerals | Met | One `@font-face` family; `tabular-nums lining-nums` on every amount, total and percent. |
| 13 journal reading measure | Met | 17.5 px / 1.72, 24 px gutters, ~38 characters per line at 390 px. `diario.png`. |
| 14 no paid typeface or icon set | Met | Lato SIL OFL 1.1, subset and self-hosted at `src/assets/fonts/`, licence copied in beside it. Every icon is a hand-drawn path in `Icon.tsx`. Test asserts the font is loaded from the repo and that `base.css` contains no `http`. |
| 15 designed empty states | Met | Today, month, journal, a chosen date, no summary, and an empty period. Six captures. |
| 16 in-progress and error for async | Met | Transcription, generation and saving each have both. |
| 17 unmistakable listening | Met | Full-takeover pulse, running clock, stop and cancel. `voz-escuchando.png`, captured **live with a fake microphone**, not staged. |
| 18 cannot-reach-server state | Met | Screen and banner. Verified on a genuine cold open with the server killed — see below. |
| 19 confirm before destroying | Met | Expense delete, journal delete, category/method removal. |
| 20 Gym present and marked | Met | `pronto` in the nav, plain Spanish placeholder, no capture bar, no request. Test asserts all four. |
| 21 peso convention | Met | One formatter; unit-tested for `$14.000`, `$1.284.500`, `$6.200`, `$0`. |
| 22 light only | Met | Zero `prefers-color-scheme` rules — asserted by test **and** by a browser-side tripwire that walks `document.styleSheets` in every capture. |
| 23 Spanish everywhere | Met | All copy in `copy/es.ts`; no string literal in any component. Tests assert the full closed error-code set is mapped, that an unknown code cannot surface untranslated, and that no common English word appears in any string. |
| 24 Spanish glyphs at every size | Met | á é í ó ú ü ñ ¿ ¡ across 11.5–46 px in the captures. The chips wrap rather than sit in a grid precisely because "Tarjeta de crédito" is 18 characters — it still fits at 320 px. |
| 25 progress that visibly changes | Met | The tally gains a stroke per second and the numeral increments. `analisis-esperando--12s.png` vs `--68s.png`. No spinner exists in the app. |
| 26 escape hatch + "on your own computer" | Met | Transcription offers **Escribir a mano** and **Cancelar from t=0**, and says "Esto ocurre en tu propio computador, no en internet." The question offers Cancelar and says leaving is allowed. |
| 27 three distinguishable summary surfaces | Met | Ready, none, generating, empty, failed — five captures, none an empty area. |
| 28 nothing implies an instant answer | Met | No determinate bar on any unbounded wait. `Tally` takes `seconds` and has **no** `total` prop, so a completion fraction cannot be passed to it even by accident. The honest-range copy is kept, as approved. |

Feel & Tone: unchanged from the approved direction. Finanzas is ruled and scans;
Diario has no rules, cards or borders at all. No gradient, no shadow except the
modal veil, no gamification, no emoji, no celebration, no moralising.

## Interface Contract Conformance

Consumed exactly as specified; types are transcribed in `src/api/types.ts` and
nothing absent from the contract is typed, so no component can render it.

| Contract entry | Where consumed |
|---|---|
| `GET /api/health` | `queries.ts:useHealth` — reachability (13.2/13.3) **and** the authoritative clock: today and this month come from `server_time`, never from the device (4.8) |
| `GET /api/status` | `Ajustes.tsx` readout, `Analisis.tsx` LLM-unavailable state (11.4) |
| `GET /api/categories`, `/api/payment-methods` | chip rows, Ajustes list; `in_use_count` drives the "en N gastos" line |
| `POST /api/categories`, `/api/payment-methods` | `GastoForm.tsx:InlineCreate` (3.2), `Ajustes.tsx:CreateInline`; `409 conflict` → "Ya tienes uno con ese nombre." |
| `PATCH /api/{kind}/{id}` | `Ajustes.tsx:EditarNombre` (3.3); success invalidates every expense view so the new name appears without a refresh |
| `DELETE /api/{kind}/{id}` | `Ajustes.tsx:askToRemove` — probes with `confirm=false`, reads **`error.details.affected_expenses`** from the `409 in_use`, composes the warning, then retries with `confirm=true` after confirmation (3.4, constraint 19) |
| `POST /api/expenses` | `GastoForm.tsx:onSubmit`; `source` sent, never read back |
| `GET /api/expenses/{id}`, `PATCH`, `DELETE` | edit and delete (5.1, 5.2) |
| `GET /api/summary/day` | `Hoy.tsx`; `total_cop: 0` with `items: []` renders the empty state, not an error |
| `GET /api/summary/month` | `Mes.tsx`; `is_empty` renders the empty state, never a zeroed chart; `percent` printed as returned |
| `POST /api/journal`, `GET`, `PATCH`, `DELETE` | `Diario.tsx`, `Entrada.tsx`; text rendered with `white-space: pre-wrap` so 6.4 survives |
| `POST /api/voice/transcribe` | `VoiceContext.tsx:transcribe` — multipart WAV 16 kHz mono per KD-15, `context` set per module, `AbortController` for 8.9 and for the 28 s client clock |
| `ExpenseDraft` | seeds the review form; `resolved_by.<field> === 'none'` is the only "needs input" signal read (9.2); `description_truncated` renders the note |
| `POST /api/expenses/suggest-category` | called **only** when `resolved_by.category === 'none'`; applied only if the field is still untouched, labelled *sugerido* (9.3, 9.4) |
| `POST /api/insights/questions` | ask box; `409 busy` opens the "cancel that one" sheet |
| `GET /api/insights/questions/{job_id}` | polled at 1 s; **`elapsed_ms` is the only progress signal read**; `answer` consumed only at `done`; `facts.journal_truncated` surfaced with both counts; `period_assumed` labelled; all six terminal `error_code` values have Spanish copy |
| `DELETE /api/insights/questions/{job_id}` | Cancelar la pregunta (11.13) |
| `GET /api/insights/summaries/latest` | all five states rendered distinctly (constraint 27) |
| `GET /api/export` | an `<a download>` to the relative path — the browser's own download, no blob held (14.2) |
| Error envelope | `ApiError` in `client.ts`; **`message` is never rendered** (KD-17). `fields[].reason` maps through `razonEnEspanol` |

`POST /api/expenses/parse` is deliberately **not** called: the contract names it a
test seam and forbids a typed natural-language expense path.

Two fields are absent by design and their absence is load-bearing: no list
distinguishes a spoken record from a typed one (9.5, 10.4), and no generated text
exists to display before `done` (KD-11).

## Verification — what was run and what it found

`node tools/shots.mjs` drives Chromium over CDP: 82 captures at 390/360/320/900 px,
forcing `:hover`, `:focus-visible` and `:active` on the **real** elements through
`CSS.forcePseudoState`. There is no `.is-hover` helper class in the app's CSS that
could drift from the real rule — the mockups needed one, the built app does not.
In each state it runs the Phase 1 audit: WCAG 2.1 contrast against the background
actually painted, every interactive box against 44×44, horizontal overflow, and a
`prefers-color-scheme` tripwire. **Current result: 82 captures, 0 findings.**

It found three real defects on the way, all invisible in a static reading:

1. **The active bottom-nav item was not violet.** `.nav a` (0,1,1) out-specified
   `.navOn` (0,1,0). Found by looking at `finanzas-hoy.png`, not by the audit.
   Fixed at `Screen.module.css:216`.
2. **The red error border lost to `:focus`** on the amount box and text inputs —
   so a rejected amount showed a violet underline while focused, which is exactly
   when it is read. Found by looking at `gasto-nuevo-error.png`. Fixed at
   `Form.module.css:36-40, 90-96`.
3. **A 178×19 touch target** — the "Ver el estado del servidor" link in the
   LLM-unavailable banner. Found by the audit. Fixed at `Analisis.tsx:103`.

Beyond the matrix, run against the **real** backend on 8001:

- **A full capture flow through the real UI** (`tools/e2e.mjs`): typed `9 900`,
  displayed `9.900`, saved; the Today total moved $83.700 → $93.600 and the row
  appeared **with no manual refresh** (2.1, 2.4, 4.6). Renaming *Ocio* to *Ocio y
  salidas* then showed the new name on the expense already filed under it (3.3).
  The rows it created were removed afterwards.
- **The service worker's actual job** (`tools/sw-warm.mjs`, then the server
  killed, then `tools/sw-cold.mjs`): a brand-new browser process cold-opening the
  app with nothing listening rendered "No puedo alcanzar tu servidor.", not
  Chrome's network error page. 11 shell entries cached, `/api/*` never. This is
  13.2's primary case and it is the reason the service worker exists.
- **Voice captured live with a fake device**: `voz-escuchando` and
  `voz-transcribiendo` are real recordings through `getUserMedia` →
  `MediaRecorder` → `decodeAudioData` → 16 kHz mono WAV, not staged screens.
- **No origin, no port, no external request in the bundle**: grepping `dist/`
  yields one URL, React's own error link. No `8000`, `8001`, `8443` or `5173`.

29 tests pass (`npm test`), including the four-interaction budget driven through
the real component tree, multi-field validation, Gym inertness, the cold-open
offline screen, the closed error-code map, and the stylesheet policy checks.

### Screenshot matrix — every row

| Row | Captured | Where |
|---|---|---|
| default | yes, all screens | `tools/shots/` |
| **hover** | yes | `*--hover`, `*--chip-hover`, `*--fila-hover`, `*--nav-hover`, `*--exportar-hover`, `*--listo-hover`, `*--boton-hover`, `*--entrada-hover` |
| **focus-visible** | yes | `*--fila-foco`, `*--chip-foco`, `*--captura-foco`, `*--monto-foco`, `*--pregunta-foco`, `*--cancelar-foco` |
| **active / pressed** | yes | `*--fila-pulsada`, `*--chip-pulsado`, `*--boton-pulsado`, `*--mic-pulsado`, `gasto-eliminar--boton-pulsado` |
| **disabled** | yes | `finanzas-mes--flecha-deshabilitada` (next month), `gasto-guardando` (submit), `analisis-ia-no-disponible` (ask field and mic), `analisis-esperando--*` (ask field and mic while a job runs) |
| empty | yes, 6 | `finanzas-hoy-vacio`, `finanzas-mes-vacio`, `diario-vacio`, `diario-fecha-vacia`, `analisis-sin-resumen`, `analisis-periodo-vacio` |
| loading | yes | `voz-transcribiendo`, `analisis-esperando--12s` / `--68s`, `analisis-generando`, `gasto-guardando` |
| error | yes, 11 | `gasto-nuevo-error` (three at once), `gasto-guardar-fallo`, `diario-escribir-error`, `voz-fallo`, `analisis-error-*` (five terminal codes), `analisis-ocupado`, `analisis-resumen-fallo` |
| narrow viewport | yes | 360 px and 320 px |
| wide viewport | yes | 900 px |
| scrolled | yes | `*--desplazado` |
| dark mode | **not applicable** | Constraint 22 is light-only. There is no dark variant that could exist: zero `prefers-color-scheme` rules, asserted by a test and by a browser-side tripwire in every capture. |

**Two states could not be captured and are named rather than written off:**

- **Microphone permission denied** (`voz-sin-permiso` in the mockups). Headless
  Chromium with `--use-fake-ui-for-media-stream` always grants; without it,
  `getUserMedia` in headless resolves rather than rejecting. The code path is
  `VoiceContext.tsx:start` → `{ kind: 'denied' }` → `VoiceScreen.tsx:Denied` and
  is reachable, but I could not make this browser produce the rejection. **QA on a
  real device should check it** — deny the permission in Chrome's site settings
  and start a voice capture.
- **`MediaRecorder` unsupported** (`{ kind: 'unsupported' }`). Same reason
  inverted: the API is present in every browser available here.

Neither is "not screenshotable" — both are unreachable *in this environment*, and
both have a named, testable path on a real Android device.

## Escalations / Deviations

No escalation was needed. Four decisions worth Reviewer's eye:

**1. The LAN fallback address is learned, not written down.** KD-2's "the frontend
hardcodes no origin… no environment-specific origin" and its instruction that the
offline state "offers a plain link to the fallback origin" cannot both be
satisfied literally. `src/state/origin.ts` stores `location.origin` whenever the
app is served over HTTPS from something other than a `.ts.net` host, and the
offline screen offers that if it exists. Setup's second home-screen icon is what
populates it. Alternative rejected: a build-time env var, which puts a port in the
bundle. **If Reviewer prefers the literal link, the address has to come from
somewhere the contract does not currently provide.**

**2. Red on the failed-save banner** — see constraint 3 above. Kept faithful to
the approved mockup and disclosed rather than silently changed.

**3. A visible "Preguntar" button** when the ask field has text — see Fidelity.
The alternative was a question that cannot be sent after being spoken.

**4. The month tabs read `Hoy` at `/finanzas` with `end`-matching.** `/finanzas`
is the landing route and also the parent of `/finanzas/mes` and
`/finanzas/analisis`; without `end` the "Hoy" tab would stay underlined on all
three.

## Acceptance Criteria Mapping

Frontend-owned criteria only; backend-owned ones are named as such.

**R1 shell** — 1.1 three destinations, part of `Screen`, test-asserted · 1.2 lands
on `/finanzas`, no splash · 1.3 Gym inert, no capture bar, no request,
test-asserted · 1.4 capture bar on Finanzas and Diario, both actions, thumb zone ·
1.5 all copy in `copy/es.ts`, closed error map test-asserted.

**R2 expenses** — 2.1 saved and visible without a refresh, verified live · 2.2 /
2.3 rejected client-side with every field named, `gasto-nuevo-error.png` · 2.4 one
parser, unit-tested, verified live with `9 900` · 2.5 one formatter · 2.6 optional
description, `null` when blank · 2.7 date input capped at the server's today;
`future_date` mapped · **2.8 four interactions, test-driven through the real
component tree**; ten categories and six methods as one-tap chips, no `<select>`
anywhere (asserted).

**R3** — 3.1 backend seeds; the UI renders whatever it returns · 3.2 inline create
inside the form, draft untouched · 3.3 rename propagates, verified live · 3.4
in-use warning from `details.affected_expenses`, confirmed before the retry · 3.5
both fields required before submit.

**R4** — 4.1 total and list newest first, each with amount, category and method ·
4.2/4.3 breakdown as returned, ordered, percentages printed · 4.4 per-method
totals · 4.5 empty month state · 4.6 TanStack invalidation on every expense
mutation, verified live · 4.7 month arrows, next disabled at the current month ·
4.8 every boundary from `server_time`; `dates.ts` reads the offset the server sent
and never the device timezone (unit-tested with an 23:00 −05:00 timestamp).

**R5** — 5.1 all five fields editable · 5.2 confirmation sheets for expense and
journal · 5.3 journal edit persists.

**R6** — 6.1, 6.2 (blank rejected inline), 6.3 (each submit is a new row), 6.4
(`pre-wrap`), 6.5 (the entry view never clamps; the *list* clamps at 7 lines with
an explicit "Seguir leyendo" — a reading of 6.5 worth stating), 6.6 (text only),
6.7 (backend round-trip; rendered unchanged).

**R7** — 7.1 grouped by day, newest first · 7.2 `/diario/fecha` with day arrows
and an explicit nothing-written state · 7.3 inviting empty state.

**R8** — 8.1 listening takeover with stop and cancel · 8.2 transcript shown before
anything is written · 8.3 cancel issues no request · 8.4 failure copy per code,
retry and manual both offered · **8.5 permission denial — path built, not
capturable here; QA must check on device** · 8.6 nothing saves until the form is
submitted · 8.7 backend · 8.8 working state immediately, 28 s client abort inside
the 30 s bound · 8.9 "Escribir a mano" from t=0 via `AbortController`.

**R9** — 9.1 draft seeds the form · 9.2 `resolved_by === 'none'` leaves the field
empty and marks it · 9.3 backend · 9.4 `categoryTouched` ref: a late suggestion
never overwrites a touched field · 9.5 nothing in any list distinguishes source ·
9.6, 9.7 backend.

**R10** — 10.1 full transcript into the editor · 10.2 rendered verbatim, no
client-side rewriting · 10.3 edits are what is sent · 10.4 indistinguishable.

**R11** — 11.1-11.3, 11.6-11.9, 11.14, 11.17 backend; the UI renders what it
returns · 11.4 explained banner, ask box disabled, everything else works · 11.5
in-progress state, result or explicit failure · 11.10 typed and spoken · 11.11 the
five terminal codes as Spanish copy that never invents a figure · 11.12 the job id
is stored in `sessionStorage` so a reload re-attaches; polling at 1 s keeps the
state alive · 11.13 cancel, and leaving the screen is explicitly allowed · 11.15
`/latest` is read on open and never triggers generation · 11.16 `none` and `empty`
as distinct surfaces · 11.18 period label and `generated_at`.

**R12** — no paid dependency; the font is SIL OFL and in the repo.

**R13** — 13.1 a web app plus manifest, no store · 13.2 cold-open state, verified
with the server killed · 13.3 health keeps polling and the banner clears itself;
jobs re-attach · 13.4 relative paths only, so both origins behave identically ·
13.5 a failed save keeps the form exactly as typed and offers retry · 13.6, 13.7
backend/ops · 13.8 the banner links to the offline screen in one action.

**R14** — 14.1, 14.3 backend · 14.2 export from Ajustes.

**R15** — 15.1-15.5 backend and ops. The frontend's half: **the bundle loads no
remote asset and makes no outbound request** — font self-hosted, icons inline SVG,
no CDN, no analytics, no Google Fonts. Grep-verified against `dist/`.

## What I did not do

- **No server-side code.** `backend/`, `ops/` and `factory/architect/design.md`
  are untouched.
- **No Gym anything.** No route content, no request, no capture control.
- **No offline queue.** The service worker precaches the shell and treats
  `/api/*` as `NetworkOnly`; there is no write queue, no background sync and no
  cached API response, per KD-13 and A15.
- **No test was deleted or weakened.** The Phase 1 audit was carried forward and
  strengthened: it now runs against the real app under forced pseudo-states
  rather than against static HTML with mirrored helper classes.

## On the handover

The Phase 1 artifacts were sufficient to rebuild from without guessing. The
design note's constraint-by-constraint table, the four-interaction budget table
and the waiting-state table were the three most load-bearing pieces;
`mockups/_build/css.py` and `build.py` meant the token system and every Spanish
string could be carried across rather than reinvented. One gap worth recording
for the template: **the mockups' inline styles were outside the reach of the
Phase 1 note's own `grep`-based constraint-3 claim**, which is how the red
save-failure banner went unlisted. A constraint claim that says "grep the
stylesheet" should say which files it grepped.
