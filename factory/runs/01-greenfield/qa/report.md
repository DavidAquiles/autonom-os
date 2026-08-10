> **Persisted by the orchestrator, not by QA.**
> QA's `Write` to this path was blocked by the harness ("Subagents should return
> findings as text") — the fourth such block in this run, after three for the
> artifact-analyst. QA returned the complete report as chat text and the
> orchestrator wrote it here **unedited** — no summarizing, no reordering, no
> trimming. Treat the body below as QA's own words.
>
> The only change made to the returned text was restoring HTML entities
> (`&lt;` → `<`, `&gt;` → `>`, `&amp;` → `&`) that the transport had escaped.
> That is a rendering repair, not a content edit.
>
> **Orchestrator-verified, because QA could not verify its own artifacts:**
> the evidence QA cites exists on disk — `/home/david/qa-shots/` contains 60
> screenshots, and `/home/david/qa-evidence/` contains `qa-autonomos.db`,
> `qa-export.json`, `qa-ss.txt`, `qa-strace-api.txt` and
> `qa-strace-whisper.txt`. The user's own `data/autonomos.db` was not used for
> testing.

---

# QA report — Autonom-OS

**Verdict: 4 acceptance criteria FAIL (9.2, 11.1, 11.2, 11.15). 2 criteria and 1 sub-clause UNVERIFIED (8.7, 13.4, and the spoken half of 9.6/9.7). Everything else passes.**
No Design Constraint fails; 27 pass, 1 (constraint 3) passes with the already-deferred F5 disclosure carried forward.

Method: the software was run for real. One backend process (`data/qa-autonomos.db`, a **fresh** database so first-run behaviour could be verified), the real whisper.cpp sidecar, the real Ollama `qwen2.5:3b-instruct-q4_K_M`, and the built SPA served from `http://127.0.0.1:8001`, driven through headless Chromium over CDP at a 390×844 phone viewport. 60 screenshots in `/home/david/qa-shots/`. Raw evidence in `/home/david/qa-evidence/`.

**Deterministic gates re-run by me at HEAD `528459e`**, not merely read from `state.json`: backend `pytest -q` → **247 passed**; frontend `npm test` → **35 passed**. `state.verification` records `test_integrity` **pass** (201 tests / 495 assertions across 21 files, no drop from 179/437). Evidence integrity is intact — no test was removed or weakened.
One bookkeeping oddity, not a product defect: every gate in `state.verification` is stamped `rev: e481fd0`, two commits behind HEAD, although the recorded counts match the later commit `f50e84d`. The gates do pass at HEAD — I ran them.

**Where I contradict the chain.** The frontend note and Reviewer both recorded criterion **8.5 (microphone permission denied) as unreachable in this environment**. It is reachable: driving `Browser.setPermission {name:'microphone', setting:'denied'}` over CDP against a Chromium started *without* `--use-fake-ui-for-media-stream` produces a real `NotAllowedError`, and the app's denial screen renders correctly. **8.5 is a verified Pass, not an Unverified.** A role that runs the software beats a role that reads it.

---

## Acceptance Criteria

Rework-cycle notes are recorded per criterion. Unless stated, a criterion passed on the first build with no rework.

### Requirement 1 — App shell and navigation

| # | Verdict | Evidence |
|---|---|---|
| 1.1 | **Pass** | `nav` carries exactly three `<a>`: `Finanzas → /finanzas`, `Diario → /diario`, `Gimnasio (pronto) → /gimnasio`. Clicked each in turn from three different screens; each landed in one interaction. The nav is present on every route audited (12 routes × 2 viewports), including the Gym placeholder, the offline screen and every voice state. |
| 1.2 | **Pass** | Navigating to `/` redirects to `/finanzas` and renders a usable Today screen. No splash, no setup step, no selection. Against an **empty** database it still lands usable (`01-landing.png`). |
| 1.3 | **Pass** | `/gimnasio` renders "Todavía no está disponible." + "Este espacio queda reservado para el gimnasio…". Counted in the live DOM: `inputs: 0, buttons: [], forms: 0`; capture bar absent; no error; no `/api/*` request made by that route. `02-gimnasio.png`. |
| 1.4 | **Pass** | Finanzas and Diario both carry a two-control capture bar ("Anotar gasto"/"Escribir" + mic) in the module itself; both open in-module without leaving it. |
| 1.5 | **Pass** | Every screen and every error I could provoke is Spanish: validation ("Escribe un monto mayor que cero.", "Elige una categoría.", "Elige un método de pago.", "Escribe algo antes de guardar.", "No puedes anotar un gasto en una fecha futura.", "Ya tienes uno con ese nombre.", "Escribe un nombre."), transcription failure, `period_unrecognised`, `llm_unavailable`, failed save, unreachable server. No English string reached any screen — including the one case where the API's `message` field carried an English exception (defect D5): the UI never renders `message`, and showed Spanish. |

### Requirement 2 — Manual expense capture

| # | Verdict | Evidence |
|---|---|---|
| 2.1 | **Pass** | Typed `14.000`, chose Comida + Efectivo, saved. Today went `$0 → $14.000` and the row appeared with **no** manual refresh or re-navigation (`11-hoy-tras-guardar.png`). |
| 2.2 | **Pass** | Empty submit → "Escribe un monto mayor que cero." inline under MONTO. `0` → same. A minus sign cannot be entered (stripped by the field); the API independently rejects `-500` with `{"field":"amount_cop","reason":"must_be_positive"}`. `12-gasto-error-vacio.png`. |
| 2.3 | **Pass** | Same submit named all three missing fields simultaneously: amount, "Elige una categoría.", "Elige un método de pago." |
| 2.4 | **Pass** | Typed into the live field: `14000` → `14.000`; `14 000` → `14.000`; `14.000` → `14.000`. All three save as 14000 (verified in the API response). |
| 2.5 | **Pass** | Every app-rendered amount across all screens: `$0`, `$14.000`, `$55.800`, `$506.500`, `$1.284.500`, `$1.349.700` — dot separator, no cents. Computed style on amount nodes is `lining-nums tabular-nums`. (See D4: amounts *inside LLM-generated summary prose* are not produced by this formatter and one summary wrote `346,000`. Flagged to PM rather than judged, since 2.5's reach into model prose is PM's call, not mine.) |
| 2.6 | **Pass** | Saved with the description left blank → stored `description: null`, 201. Saved with a description → stored verbatim. |
| 2.7 | **Pass** | `input[type=date]` carries `max=2026-08-06`. Forcing `2026-12-25` past the picker and submitting → "No puedes anotar un gasto en una fecha futura.", nothing saved (`GET /api/expenses?month=2026-12` → `total_count 0`). Backdating to `2026-08-02` accepted and saved. `44-fecha-futura.png`. |
| 2.8 | **Pass — exactly 4** | Counted taps in the running UI from the default screen: **1** "Anotar gasto" → form opens with `document.activeElement` = the Monto field (so no tap is spent focusing it) → type the amount (excluded) → **2** category chip → **3** method chip → **4** "Guardar gasto". `document.querySelectorAll('select').length === 0`; all 16 categories/methods are one-tap chips. Budget met with nothing to spare. `10-gasto-nuevo.png`. |

### Requirement 3 — Categories and payment methods

| # | Verdict | Evidence |
|---|---|---|
| 3.1 | **Pass** | Against a database created empty by this run: 10 Spanish categories (Comida, Transporte, Mercado, Servicios, Salud, Ocio, Hogar, Ropa, Educación, Otros) and 6 payment methods (Efectivo, Tarjeta de crédito, Tarjeta débito, Transferencia, Nequi, Daviplata). |
| 3.2 | **Pass** | Inside the form with `33.300` already typed: "Nueva" → typed "Mascotas" → "Crear y elegir". The amount survived (`33.300`), the new chip appeared **already selected**, and the sheet says "Lo que ya escribiste se queda como está." Saved with the new category. `40-categoria-inline.png`. |
| 3.3 | **Pass** | Renamed *Mercado* → *Mercado y víveres* in Ajustes; the expense already filed under it showed the new name on the Today list and in the month breakdown without a refresh. |
| 3.4 | **Pass** | Removing an in-use category warns with the count: "«Mercado y víveres» está en 2 gastos… Esos 2 gastos se quedan como están y siguen contando en los totales, con el nombre «Mercado y víveres». Lo único que cambia es que ya no vas a poder elegirlo al anotar." After confirming: both expenses still present and still attributed to that name in Today and in the month breakdown; the chip is gone from the form and the row gone from Ajustes. `42-quitar-en-uso.png`. (See D7 — the API alone will still accept an archived id; not reachable through the UI.) |
| 3.5 | **Pass** | Chips are `role="radio"` in a `radiogroup`. Clicking Comida then Transporte, Efectivo then Nequi leaves exactly `["Transporte","Nequi"]` checked. Neither can be zero: submit is rejected naming the field. Schema-level, both FKs are NOT NULL. |

### Requirement 4 — Today and this month

| # | Verdict | Evidence |
|---|---|---|
| 4.1 | **Pass** | Today: `$55.800`, "3 gastos anotados hoy", rows newest-first (12:37 Mercado, 12:37 Transporte, 12:36 Comida), each showing amount, category and payment method. `20-hoy.png`. |
| 4.2 | **Pass** | August: `$506.500`, "8 gastos", "EN QUÉ SE FUE" with per-category amount and percent. `21-mes.png`. |
| 4.3 | **Pass** | Percentages summed to exactly 100 in every state I produced: 51+24+9+7+6+3; 48+22+11+6+6+6+1; 67+28+5 (July); 52+27+13+8 (June). Ordered largest→smallest every time. |
| 4.4 | **Pass** | "CÓMO SE PAGÓ": Tarjeta débito $260.000, Transferencia $120.000, Tarjeta de crédito $77.000, Efectivo $32.500, Nequi $17.000 — sums to the month total. |
| 4.5 | **Pass** | Empty August on a fresh DB: "En agosto no hay gastos anotados. Cuando anotes el primero, aquí verás en qué se fue el mes y cómo lo pagaste." Navigating to June (no data): "En junio no hay gastos anotados." No `NaN`, no `0%` rows, no blank screen, no error. `04-finanzas-mes-vacio.png`. |
| 4.6 | **Pass** | Save: Today `$0 → $14.000`. Edit (9.800→12.500, moved to Aug 4): Today `$55.800 → $46.000`, month `$506.500 → $509.200`. Delete: Today `$79.300 → $46.000`. All on next view, no manual refresh. |
| 4.7 | **Pass** | One tap of "Mes anterior" → julio 2026, `$313.000`, full breakdown and payment-method totals on the same terms; one tap of "Mes siguiente" → back to agosto. "Mes siguiente" is `disabled` while on the current month. `22-mes-julio.png`. |
| 4.8 | **Pass** | Ran a server with `APP_TZ=Pacific/Kiritimati` while UTC was `2026-08-06 18:19`. `/api/health` → `2026-08-07T08:19+14:00`; `/api/summary/day` → `2026-08-07`; an expense created at that moment → `spent_on: 2026-08-07`. In the **browser**, whose own device clock read `Thu Aug 06 2026 … GMT-0500`, the UI header showed **"viernes 7 de agosto"**. The app takes the calendar from the server's configured local timezone, not from UTC and not from the device — exactly the 11pm-belongs-to-that-day property. |

### Requirement 5 — Correcting the record

| # | Verdict | Evidence |
|---|---|---|
| 5.1 | **Pass** | Opened an existing expense (form pre-filled: `monto 14.000`, chips `["Comida","Efectivo"]`). Changed all five fields; `GET /api/expenses/2` afterwards: `12500 / Ocio / Daviplata / 2026-08-04 / "Editado por QA"`, `updated_at` moved. |
| 5.2 | **Pass** | Expense: "¿Eliminar este gasto? Deja de contar en el total de hoy y en el del mes. No se puede deshacer." with the expense summarised. Cancel → count unchanged (3 → 3). Confirm → 3 → 2, total `$79.300 → $46.000`. Journal: "¿Eliminar esta entrada?" — cancel left 5 entries, confirm left 4. `43-gasto-eliminar.png`, `33-diario-confirmar-borrado.png`. |
| 5.3 | **Pass** | Edited an entry to "Texto editado por QA — ñ á ¿¡"; re-read from the API after the fact, persisted byte-for-byte. |

### Requirement 6 — Journal capture

| # | Verdict | Evidence |
|---|---|---|
| 6.1 | **Pass** | Saved text appears at the top of the list under "JUEVES 6 DE AGOSTO" with its time. |
| 6.2 | **Pass** | `"     \n\t  "` → "Escribe algo antes de guardar.", nothing written. `30-diario-error.png`. |
| 6.3 | **Pass** | Two entries the same minute stayed two rows with their own times; neither merged nor overwrote the other. |
| 6.4 | **Pass** | An entry with two blank-line paragraph breaks, a single newline and leading spaces round-tripped exactly (`white-space: pre-wrap`); rendered identically on re-open. |
| 6.5 | **Pass** | Saved a **10.210-character** entry. `GET /api/journal` returns `text.length === 10210`; the entry view's rendered text node is also `10210` and contains "Párrafo 120". The *list* clamps with an explicit "Seguir leyendo" — the entry itself is never truncated. `32-diario-entrada-larga.png`. |
| 6.6 | **Pass** | The editor has exactly one field (`textarea`, placeholder "Lo que estés pensando…") and a Guardar button. No title, category, tag or mood. |
| 6.7 | **Pass** | "¡Qué día tan raro! … mi mamá … ñandúes … ¿Será que exagero?" stored and redisplayed unchanged; accented vowels, ñ, ¿ and ¡ all intact at every rendered size. |

### Requirement 7 — Journal browsing

| # | Verdict | Evidence |
|---|---|---|
| 7.1 | **Pass** | Newest first, grouped under an uppercase date heading ("JUEVES 6 DE AGOSTO"). |
| 7.2 | **Pass** | `/diario/fecha` shows the chosen day's entries; stepping back one day gives "No escribiste nada el miércoles 5 de agosto. Puedes moverte a otro día con las flechas, o volver a todas las entradas." `34-diario-fecha-vacia.png`. |
| 7.3 | **Pass** | Empty journal: "El diario está vacío. Escribe lo que estés pensando. No hace falta título, ni categoría, ni ánimo del día: solo el texto." `05-diario-vacio.png`. |

### Requirement 8 — Voice capture (shared)

| # | Verdict | Evidence |
|---|---|---|
| 8.1 | **Pass** | Full-screen takeover: "Te estoy escuchando", a running clock (`0:01`, `0:03`), "máximo 30 segundos", and both **Listo** and **Cancelar**. Unmistakable against the idle screen. `50-voz-escuchando.png`. |
| 8.2 | **Pass** | "ESTO FUE LO QUE ESCUCHÉ" with the transcript in quotes, above the form, and "Nada se guarda hasta que toques Guardar." `55-voz-revision.png`. |
| 8.3 | **Pass** | Cancelled mid-recording: **zero** network requests (`/api/voice/transcribe` never fired), expense and journal counts unchanged (3 gastos / 4 entradas before and after). |
| 8.4 | **Pass** | Real failure, not simulated: the fake capture device produces non-speech, whisper returns nothing usable, and the app shows "No entendí lo que dijiste. El audio llegó, pero salió vacío…" with **Grabar otra vez** and **Escribir a mano**, plus a hint pointing at Ajustes → Tu servidor. Nothing was written. `53-voz-resultado.png`. |
| 8.5 | **Pass** — *previously recorded as unreachable* | Chromium started **without** `--use-fake-ui-for-media-stream`, then CDP `Browser.setPermission {microphone: denied}`. `getUserMedia` → `REJECTED: NotAllowedError` (confirmed in-page). The app shows "El navegador no me deja usar el micrófono. El permiso está bloqueado para esta dirección. Puedes cambiarlo en los ajustes del navegador, en Permisos del sitio. Mientras tanto, anotar a mano funciona igual que siempre." and **Escribir el gasto a mano** lands on a fully working manual form. `90-voz-sin-permiso.png`. |
| 8.6 | **Pass** | No path writes a record from audio. The review form is always interposed; the copy states it; the transcribe endpoint returns a transcript and writes nothing (counts unchanged across every transcription I ran). |
| 8.7 | **Unverified** | This host has no microphone and no Spanish TTS. I will not synthesize speech and call it a pass. What I can say: the sidecar runs with `-l es`, no translate flag exists in this build, and every transcript path returns Spanish. **Someone with a microphone must still say one Colombian Spanish sentence into it.** |
| 8.8 | **Pass** | Short clip: working state at **267 ms / 308 ms / 250 ms** (three runs), terminal at **5.8 s / 6.3 s / 6.6 s**. Full-length utterance: recording auto-stopped at **30.2 s**, working state at **250 ms**, explicit terminal at **6.6 s** after the recording ended. Both bounds (1 s, 30 s) met with wide margin, including a contended run (6.3 s while an LLM answer was being preempted). |
| 8.9 | **Pass** | Mid-transcription "Escribir a mano" switched to `/finanzas/gasto/nuevo` in **1.24 s**, with a usable Monto field; no waiting for the transcription to finish. `58-escribir-a-mano.png`. |

### Requirement 9 — Voice to expense

The audio→text step is the one thing this host cannot produce honestly. For 9.1–9.5 I obtained the **real** draft from the **real** backend parser (`POST /api/expenses/parse`) and served it as the transcribe response; every layer after transcription is the real running system. This is disclosed, not hidden.

| # | Verdict | Evidence |
|---|---|---|
| 9.1 | **Pass** | "gasté 14.000 pesos en Uber con la tarjeta de crédito" → review form pre-filled `monto 14.000`, category **Transporte** tagged *SUGERIDO*, method **Tarjeta de crédito**, description = the sentence. `55-voz-revision.png`. |
| 9.2 | **FAIL** | See defect **D1**. The *payment method* is correctly left empty and marked with a "FALTA ELEGIRLO" pill on a highlighted region. The *amount* and the *category* are not. "gasté cinco mil, no sé en qué" → CATEGORÍA renders with **no marker at all**, indistinguishable from a satisfied field (`57-voz-revision-sinCat.png`). "compré algo" → MONTO is empty with **no marker**, showing a grey `$ 0` placeholder (`57-voz-revision-compreAlgo.png`). The criterion requires empty **and visibly marked as needing input**; only one of three fields does both. |
| 9.3 | **Pass** | Every suggestion I could elicit was an existing row: `Transporte`, `Comida`, `Ropa`, `Otros` — all returned as `category_id` from the user's own list. Nonsense text (`"xyzzy plugh"`, `"hoy fue un día raro"`) returns `{"category_id": null, "source": "none"}` rather than an invented name. |
| 9.4 | **Pass** | Changed the pre-filled `14.000 / Transporte` to `15.500 / Ocio` before confirming; the saved row is `15500 / Ocio`, not the suggestion. |
| 9.5 | **Pass** | The saved voice expense is a row identical in form to a typed one — same fields, same Today and month totals, same edit route. Nothing in any list distinguishes source (`source` is request-only and appears in no list response). |
| 9.6 | **Pass** *(resolution verified with text; the spoken input path is Unverified — see 8.7)* | Through the real backend: `14.000` → 14000, `catorce mil` → 14000, `14 mil` → 14000, `un millón doscientos mil` → 1200000. |
| 9.7 | **Pass** *(same caveat)* | "con la tarjeta de crédito" → Tarjeta de crédito; "en efectivo" → Efectivo; "con la tarjeta débito" → Tarjeta débito. When no method is named ("14 mil en transporte") the field is `null` with `resolved_by.payment_method = "none"` — matched or empty, never guessed. |

### Requirement 10 — Voice to journal

| # | Verdict | Evidence |
|---|---|---|
| 10.1 | **Pass** | The whole transcript lands in the editor for review; the screen says "Son tus palabras, sin corregir ni resumir. Puedes editarlas antes de guardar." `59-diario-voz-revision.png`. |
| 10.2 | **Pass** | Compared in-page: `textarea.value === transcript` → **true**, byte-for-byte, including the blank-line paragraph break, the accents and "¿Será que exagero?". No summarising, rewriting or translation. Structurally, no LLM call exists on the journal voice path — the transcribe response for `context=journal` carries `draft: null`. |
| 10.3 | **Pass** | Appended "Postdata editada por QA." before confirming; the stored text is the edited version. |
| 10.4 | **Pass** | The spoken entry sits in the list indistinguishable from typed ones and opens in the same editor. |

### Requirement 11 — Insights

All against **real recorded data** and the real local model.

| # | Verdict | Evidence |
|---|---|---|
| 11.1 | **FAIL** | See defect **D2**. Asked "¿qué me ha preocupado este mes?" seven times against five real journal entries. Four answers were properly grounded. **Three contained a clause supported by nothing in the record**: "…También has estado reflexionando sobre tus **ingresos vs desembolsos semanales**" (no entry mentions income, which is out of scope entirely); "…e **Inversión en la inversión futura**"; "…el **miedo a perder dinero** en estos gastos semana tras semana". These are facts asserted about the user that he did not record. The design names this surface as prompt-enforced and unguarded, and asked QA to judge it; this is the judgement. |
| 11.2 | **FAIL** | Every *deterministic* figure matched exactly, repeatedly: "Gastaste 37.500 pesos en Comida este mes" vs the month screen's Comida `$37.500`; "260.000 pesos en Ropa" vs `$260.000`; the July summary's 313.000 / 210.000 / 67% / 88.000 / 28% / 15.000 / 5% and its payment split all match `finanzas/mes` for July; the June summary's 346.000 / 180.000 / 95.000 / 45.000 / 26.000 and their dates all match June's month view. **But** the July summary opens "el usuario gastó un total de 313.000 pesos durante los días con algún gasto **(20)**". Nothing on the Finanzas screen is 20 — July shows *3 gastos* across 3 days. The token passes NumericGuard because `20` is a member of the fact set for an unrelated reason (the 20 July top-expense date), the documented membership-not-meaning limit. A stated figure that matches nothing is what this criterion forbids. Defect **D8**. *(Only this one figure out of every figure produced in 2 summaries and 12 answers.)* |
| 11.3 | **Pass** | "¿cuánto gasté en junio?" (no June data) → `failed / insufficient_data` in **9 ms**, and no model call at all. "¿qué me preocupaba en julio?" (no July journal) → "No puedo responder con lo que hay registrado." in 4.8 s. |
| 11.4 | **Pass** | Ran the server with a dead `LLM_BASE_URL`. `/api/status` → `llm: "unavailable"`; `POST /api/insights/questions` → `503 llm_unavailable`. The UI shows "El modelo de texto de tu computador no responde. No se pueden hacer preguntas ni escribir resúmenes ahora mismo. Anotar gastos, escribir en el diario y ver tus totales funciona igual que siempre." with the ask field `disabled`. With the model down I then saved an expense (`$63.000 → $65.200`), saved a journal entry (5 → 6), and read Today, Mes and Diario normally. The already-produced summary stayed readable. Ajustes reports "Modelo de texto: no disponible". `91-ia-no-disponible.png`. |
| 11.5 | **Pass** | "Pensándolo en tu computador" with a second-by-second counter; terminates in either an answer or a named failure. All five terminal codes I could reach (`preempted`, `period_unrecognised`, `insufficient_data`, `llm_unavailable`, plus the answered case) render distinct Spanish surfaces. |
| 11.6 | **Pass** | Fingerprinted month total, expense count, entry count and every entry length before and after asking and cancelling: `529700/10 | entradas 5 | 156,54,113,78,94` — byte-identical. No insight path writes to `expenses` or `journal_entries`. |
| 11.7 | **Pass** | Every answer and both summaries were in Spanish. |
| 11.8 | **Pass** | "¿cuánto gasté en comida este mes?" → "Gastaste 37.500 pesos en Comida este mes." in 20 s; the Finanzas month screen showed Comida `$37.500`. Also "¿cuánto gasté en ropa este mes?" → 260.000, matching. *(Passed only after one rework cycle — Reviewer F3, the guard was rejecting figures its own prompt had authorised.)* |
| 11.9 | **Pass** | "¿qué me ha preocupado este mes?" → answers drawn from the actual entries ("la cantidad de dinero gastada en Mercado y víveres… tus pensamientos sobre la plata que se va en compras semanales", "las conversaciones con tu mamá"), `facts.journal_entries_used: 5 de 5`, period "agosto de 2026". Answered from the journal for the named period. The grounding defect is recorded under 11.1, not here. |
| 11.10 | **Pass** | Typed: verified throughout. Spoken: the ask row carries "Preguntar con la voz"; it opens the same listening takeover ("Pregunta por voz / Te estoy escuchando / 0:01 / máximo 30 segundos / Listo") and on transcript the question is quoted on screen and generation begins. `94-pregunta-por-voz.png`. |
| 11.11 | **Pass** | "¿cuánto gasté en gasolina este mes?" (no such category) → "No puedo responder con lo que hay registrado." "¿qué escribí sobre mi jefe este mes?" (never written) → same, with no invented quotation. "¿cuánto gasté en los últimos tres meses?" → `period_unrecognised` in **8 ms** and the UI says "No entendí de qué periodo hablas. Prueba nombrando un mes, «este mes» o «el mes pasado»." No figure, date or quotation was ever fabricated in these cases. *(Passed after one rework cycle — Reviewer F3.)* `92-analisis-error-periodo.png`. |
| 11.12 | **Pass** | Working state at **315 ms** and **413 ms** (two UI runs), well inside 1 s. The state stays alive — a per-second counter and changing labels, never a frozen spinner. Answers returned in 4, 5, 16, 16, 20, 22, 36 s; every terminal state inside 120 s. *(This is the criterion that needed the most rework: Reviewer F1 found the NumericGuard retry escaped the deadline entirely, and the backend's **first** fix was reverted by the coordinator because it would have handed the provider a ~1.78e9-second timeout — with all 231 tests still green against that broken state. It took two attempts plus a new test that asserts the quantity rather than the outcome. It passes now; it did not pass cheaply.)* |
| 11.13 | **Pass** | "Cancelar la pregunta" mid-generation returned to the summary view; the data fingerprint was unchanged. Separately, navigating away mid-answer worked, Diario stayed usable, an expense saved in 2.5 s while the answer was still generating, and returning to `/finanzas/analisis` re-attached to the job and showed the finished answer. |
| 11.14 | **Pass** | Nobody asked. The in-process scheduler scanned, found July complete with data, and wrote the summary on its own (log: `summary 2026-07 -> ready`). It covers spending **and** journal — the July text ends "No hubo entradas diarias en este período", and `facts.domain` is `both`. |
| 11.15 | **FAIL** | The primary case passes convincingly: opening `/finanzas/analisis` rendered the completed July summary **3 ms** after load, with no generation triggered (`/latest` is a row read). **But** in a second, reachable state it fails. On a database where June has data and July has none, the scheduler produced *both* a `ready` June summary (correct figures, verified against June's month view) *and* an `empty` July row. `GET /api/insights/summaries/latest` returns the July `empty` row, and the UI shows "Julio de 2026 no tiene nada anotado." — the completed June summary is **not readable anywhere in the app**, and no endpoint exists to reach it. One month of not using the app permanently hides the last real summary. Defect **D3**. `A0-resumen-oculto.png`. |
| 11.16 | **Pass** | Both disjuncts observed live. Never produced: "Todavía no hay ningún resumen. El primero se escribe solo cuando termine el mes. No tienes que pedirlo ni esperarlo aquí." Period with no data: "Julio de 2026 no tiene nada anotado. Sin gastos y sin entradas de diario no hay resumen que escribir. El del mes en curso se intentará cuando termine." Neither is blank and neither is a fabricated summary. `06-analisis.png`, `95-resumen-periodo-vacio.png`. |
| 11.17 | **Pass** | Caught it happening in the wild rather than staging it: at 12:49:32 the scheduler began the July summary; at 12:49:34 a real transcription arrived and the log records `arbiter cancelled SUMMARY (superseded)`. The transcription completed normally and the summary retried and completed at 12:51:02. Separately, an expense saved in 2.5 s while an answer was generating. One note for the record: in that instance the summary did not yield within the 2 s grace and the arbiter had to `force-take` the slot (`WARNING … after the grace period`) — the backstop worked and no bound was missed, but summary preemption is not the sub-100 ms path that question preemption is. |
| 11.18 | **Pass** | "Resumen de julio de 2026 · Escrito el 6 de agosto a las 12:51" — period and production time, both stated. |

### Requirement 12 — Zero cost

| # | Verdict | Evidence |
|---|---|---|
| 12.1 | **Pass** | Backend runtime deps: fastapi, uvicorn, httpx, python-multipart, pydantic. Frontend: react, react-dom, react-router-dom, @tanstack/react-query. All free OSS. Models are local files. The whole stack ran end-to-end for two hours with no account, no licence and no metered service. |
| 12.2 | **Pass** | No credential of any kind exists: grepping config and the env template for key/token/secret/bearer/password/billing/subscription matches only `LLM_MAX_TOKENS_*`-style names. Nothing prompted for payment at any step; there is no third party to be billed by. |
| 12.3 | *Retired at the Kickoff gate.* | Not tested; number retired, not reused. |
| 12.4 | **Pass** | The only host in backend source is `127.0.0.1`. The built bundle contains no external endpoint (only XML namespace URIs and React's error-decoder link, neither fetched). Nothing in the running path can begin charging, rate-limiting or shutting down. |

### Requirement 13 — Reaching it from the phone

| # | Verdict | Evidence |
|---|---|---|
| 13.1 | **Pass** | Used entirely as a web app in a browser at `http://127.0.0.1:8001/`. No install, no store, no package. |
| 13.2 | **Pass** | Killed the server. On an already-loaded screen a banner appears: "No alcanzo tu servidor. Lo que ves puede estar desactualizado y no se puede guardar nada nuevo hasta que vuelva. Se reconecta solo." with "Ver qué hacer". On a fresh load it renders the full designed screen: "No puedo alcanzar tu servidor. Tu teléfono no encuentra el computador donde vive Autonom-OS…" with **Reintentar**. Not a blank page, not an infinite spinner, not Chrome's error page. `86-sin-servidor-con-enlace.png`, `84-sin-servidor-pantalla.png`. |
| 13.3 | **Pass** | Restarted the server; the still-open app recovered by itself — banner cleared, Today re-rendered `$63.000 / 4 gastos`. No reinstall, no clearing data, nothing lost. |
| 13.4 | **Unverified** *(partially verified)* | Tailscale is installed but not logged in, so the actual away-from-home tailnet path cannot be exercised — that step is the human's. What I did verify: one process serves both origins with an identical API and SPA — `http://127.0.0.1:8123/api/health` and `https://127.0.0.1:8444/api/health` returned identical bodies including the same `origins` block, and the SPA loaded over TLS (200). No feature is gated on which origin serves it (the client uses relative paths only). |
| 13.5 | **Pass** | Typed `77.700`, Comida, Nequi and "Texto que no se debe perder", killed the server, then submitted. The app showed "No pude guardar: no alcanzo tu servidor. Nada se perdió. Lo que escribiste sigue aquí tal como está; vuelve a intentarlo cuando el computador esté despierto." and the live form still held `{monto:"77.700", desc:["Texto que no se debe perder"], chips:["Comida","Nequi"]}`. `80-guardar-fallo.png`. |
| 13.6 | **Pass** | `ss -ltnp`: API `127.0.0.1:8001`, whisper `127.0.0.1:8081`, Ollama `127.0.0.1:11434` — all loopback. From the host's own LAN address `192.168.1.11`, all three returned `000` (refused). `LAN_BIND_ADDR=0.0.0.0` is **refused**, not obeyed: "LAN fallback origin not started: LAN_BIND_ADDR=0.0.0.0 is refused; name one interface". |
| 13.7 | **Pass** | Opening the app lands on Finanzas with the capture bar already there. No login, no passcode, no connection step, no manual action of any kind before capturing. |
| 13.8 | **Pass** *(both clauses, both directions)* | With **nothing ever learned** (`origins: {primary:null, lan:null}`), the offline screen renders the plain-Spanish instruction unconditionally — "La versión de casa funciona cuando el teléfono y el computador están en el mismo wifi, aunque no haya internet." — and **no link is invented**. After a successful `/api/health` advertising `primary`, the same screen offers "**Abrir la versión de siempre** → https://autonomos.tail1a2b3c.ts.net" plus the explanation. The screen is one deliberate action away: "Ver qué hacer" on the banner, or the always-present nav from a form. `82-sin-servidor-sin-origen.png`, `87-sin-servidor-con-enlace.png`. *(Passed after one rework cycle — Reviewer F2. Worth the human's attention: the frontend's own note had claimed this worked when there was in fact **no state of the app in which the link appeared**. It works now; I verified both directions myself rather than trusting the note.)* |

### Requirement 14 — The record survives

| # | Verdict | Evidence |
|---|---|---|
| 14.1 | **Pass** | Fingerprinted every expense and entry (`sha 174e918f…`), killed the server with SIGTERM mid-session (once ungracefully), restarted, re-fingerprinted: identical. Repeated across **9** server restarts during this session; the final pair was `16 expenses / 6 journal / 1 summary sha 7f5a416b8eca9c4a` before and after. The produced summary survived too. |
| 14.2 | **Pass** | `GET /api/export` → `content-disposition: attachment; filename="autonomos-2026-08-06.json"`, `application/json`, containing `categories`, `payment_methods`, `expenses`, `journal_entries`, `summaries` — with both ids **and** resolved names, full journal text and timestamps. Parsed and read it with plain `python3 -m json.tool`, no app involved. Reachable from Ajustes → "Exportar todo". |
| 14.3 | **Pass** | Nothing vanished across two hours, 9 restarts and a scheduler running its full tick cycle; the fingerprint is unchanged. Snapshot pruning touches only `data/snapshots`. There is no expiry or archival path over user records. |

### Requirement 15 — The data never leaves the PC

| # | Verdict | Evidence |
|---|---|---|
| 15.1 | **Pass** | Ran the API and whisper under `strace -f -e trace=connect`. Across a full session including live transcriptions, the API made **6** `connect()` calls, **all** to `127.0.0.1` (whisper :8081, Ollama :11434). whisper-server made **zero** outbound connections. Audio is forwarded in memory to loopback and never written to disk. |
| 15.2 | **Pass** | Same trace covers insight generation: the only egress is `127.0.0.1:11434`. Sampling `ss -tnp` every 250 ms through a generation showed Ollama with loopback peers only. |
| 15.3 | **Pass** | Recorded **every** URL the browser requested across a full session: all to `http://127.0.0.1:8001` — no CDN, no font host, no analytics, no telemetry. Zero non-loopback requests, in the browser or in any server process. |
| 15.4 | **Pass** | No account, no login, no API key exists anywhere in config, env template or code; the entire stack ran with none. |
| 15.5 | **Pass** | Two independent demonstrations. (a) The `strace`/socket evidence above: during a complete voice capture and a complete insight answer, **not one** socket left the machine — so no external link can be a dependency. (b) Corroboration: restarted the API with `http_proxy`/`https_proxy`/`all_proxy` pointed at a closed port and `no_proxy=127.0.0.1,localhost` (verified from that same environment: an external HTTPS request returns `000`). With the outside world unreachable to that process, a live transcription and "¿cuánto gasté en comida este mes?" → "Gastaste 39.000 pesos en Comida este mes" both completed normally. **Method limit, stated plainly:** I have no root, no sudo and no working `unshare`, so I could not physically drop the host's default route; I proved the equivalent property instead. |

---

## Visual Constraints

Checked against the running UI at 390×844 and 320×844 across 12 routes, plus targeted states. My audit is independent of the frontend's own harness: it walks the live DOM, computes each text node's contrast against the background actually painted beneath it, measures every interactive box, checks horizontal overflow, and walks `document.styleSheets` for dark-mode rules. **Result: 0 findings, both viewports, all 12 routes.**

| # | Verdict | Evidence |
|---|---|---|
| 1 white dominant | **Pass** | Every screenshot: white/near-white (`#fff`, `rgb(250,249,252)`) is the page surface everywhere. The largest violet area is the transient recording takeover, not a page background. |
| 2 violet is the only brand hue | **Pass** | Full colour inventory harvested from the live DOM across all routes: whites `255,255,255` / `250,249,252`; inks `34,27,51` / `94,87,112` / `180,174,194` / `0,0,0`; violets `74,36,168` / `90,47,206` / `122,87,220` / `154,130,231` / `182,166,239` / `203,190,243` / `213,201,246`; one red `192,24,43`. No second decorative hue exists. |
| 3 exactly one functional red | **Pass, with the deferred F5 disclosure carried forward** | `rgb(192,24,43)` is the only non-violet functional colour and it appears on destructive confirmations and validation errors. The failed-save banner also uses it — that is recorded deferral **F5**, not a new finding. I found no *other* use of red. |
| 4 violet tints for the breakdown | **Pass** | The category bars are one hue at varying tints; no unrelated colours. `21-mes.png`. |
| 5 WCAG AA contrast | **Pass** | Computed for every text node against its actually-painted background, 4.5:1 body / 3:1 large, at 390 and 320 px across 12 routes: **0 failures**, including violet-on-white and white-on-violet. |
| 6 no colour-only meaning | **Pass** | Every breakdown row prints name + amount + percent adjacent to its bar; every payment row prints name + amount. Verified in text and in `21-mes.png`. |
| 7 390 px, no h-scroll, no zoom | **Pass** | `documentElement.scrollWidth > innerWidth` is **false** on all 12 routes at 390 px and at 320 px, and still false when scrolled to the bottom of the longest screen. Smallest body text 13.5 px. |
| 8 no desktop-only layout | **Pass** | Phone-first `min(390px, 100vw)` column; renders identically centred at wider viewports. No fixed desktop width. |
| 9 thumb-zone capture | **Pass** | Measured in the live DOM at 390×844: "Anotar gasto" `top 712, bottom 764, 280×52`; mic `top 709, bottom 767, 58×58`. Both entirely in the bottom ~135 px, on both Finanzas and Diario. |
| 10 ≥44×44 targets | **Pass** | Every interactive box on all 12 routes at both viewports measured: **0** under 44×44. |
| 11 three destinations everywhere | **Pass** | Exactly three `nav` links on every route audited, including Gimnasio, the offline screen, the voice takeover and every form. |
| 12 one family, aligned numerals | **Pass** | The only family rendering text anywhere is **Lato**. Amount nodes compute `font-variant-numeric: lining-nums tabular-nums`, so column figures align. |
| 13 journal reading measure | **Pass** | Measured on a real entry: `17.5 px / 30.1 px line-height`, 342 px measure, ≈34 characters per line. A reading setting, not a table row. |
| 14 no paid typeface or icon set | **Pass** | Lato (SIL OFL) self-hosted from the repo; the four woff2 files load from `127.0.0.1:8001/assets/`. No icon font — icons are inline SVG paths. No external font request was made in any session. |
| 15 designed empty states | **Pass** | All five observed live and captured: Today with no expenses, current month with no expenses, empty Journal, a chosen date with nothing written, and insights with nothing yet (plus the empty-period surface). None blank, none an error, none a zeroed chart. |
| 16 in-progress + error for async | **Pass** | Transcription: "Enviando al computador" → "Transcribiendo en tu computador" with a counter, and the "No entendí lo que dijiste" error. Insight: "Pensándolo en tu computador" with a counter, and five distinct Spanish terminal-error surfaces. Saving: the disabled/saving state, and "No pude guardar: no alcanzo tu servidor." |
| 17 unmistakable listening | **Pass** | Full-screen takeover, "Te estoy escuchando", running clock, **Listo** and **Cancelar**. Cannot be confused with idle. `50-voz-escuchando.png`. |
| 18 cannot-reach-server state | **Pass** | Both a banner and a designed screen, in plain Spanish, with no raw technical error anywhere. Verified against a genuinely dead server. |
| 19 confirm before destroying | **Pass** | Expense delete, journal delete and category removal all interpose a confirmation; cancelling each one left the data untouched (verified by count, not by looking). |
| 20 Gym present and marked | **Pass** | "Gimnasio" in the nav with a "PRONTO" label; the screen states it plainly and carries no control, no list, no error and no request. |
| 21 peso convention | **Pass** | Every app-rendered amount, across every screen and both viewports, is `$1.284.500` form with no cents. *(D4 concerns amounts inside LLM-generated prose, which this formatter does not touch; flagged to PM rather than judged here.)* |
| 22 light only | **Pass** | Walked `document.styleSheets` on all 12 routes at both viewports: **zero** `prefers-color-scheme` rules. No theme toggle exists in the UI. |
| 23 Spanish throughout | **Pass** | Every label, button, placeholder, empty state and error observed is Spanish, including every error I could provoke. No mixed-language string reached a screen. |
| 24 Spanish glyphs at every size | **Pass** | á é í ó ú ü ñ ¿ ¡ render correctly from 11.5 px uppercase labels to the 46 px total — "Educación", "Tarjeta de crédito", "¡Qué día tan raro!", "ñandúes", "¿Eliminar esta entrada?". No clipping, no substituted glyph, no broken layout at 320 px. |
| 25 progress that visibly changes | **Pass** | Transcription: label changes "Enviando al computador" → "Transcribiendo en tu computador" and a seconds counter increments (observed 0→1→2→3→4→5). Insight: a per-second tally. No static spinner exists anywhere in the app. |
| 26 escape hatch + "on your own computer" | **Pass** | The transcription wait offers **Cancelar** and **Escribir a mano** from t=0 (I used it at 1.24 s) and says "Esto ocurre en tu propio computador, no en internet." The insight wait offers **Cancelar la pregunta** and says "Puedes irte de esta pantalla; cancelar no borra nada de lo que tienes guardado." |
| 27 three summary surfaces | **Pass** | Four of the five states seen live and captured, all visually distinct, none an empty area: **ready**, **none**, **generating** (caught during the scheduler's real run at 12:49–12:50), **empty**. The three the constraint names were all observed. |
| 28 nothing implies an instant answer | **Pass** | Copy sets honest expectations: "suele tardar cerca de un minuto", "Con un mensaje corto suele tardar entre 7 y 15 segundos". No determinate progress bar on any unbounded wait; no animation or affordance implying immediacy. |

*Feel & Tone is guidance and I have not marked it. For the record only: the built app matches the brief's intent — Finanzas scans, Diario is quieter and roomier, no gradients, no gamification, no emoji, no moralising about spending.*

---

## Edge Cases Exercised

- **Amount boundaries.** `0`, negative (via the API), a 21-digit integer, an amount as a JSON string (`"14000"` — accepted and coerced), `1.284.500` and `1284500` typed into the live field.
- **Date boundaries.** Future date forced past the picker's `max`; backdating; a server timezone whose calendar day differs from UTC's; the next-month arrow at the current month.
- **Journal boundaries.** Whitespace-only, 10.210 characters, multiple paragraph breaks and leading whitespace, accents/ñ/¿¡, two entries in the same minute, edit-then-delete, cancel-delete.
- **Category/method lifecycle.** Duplicate name (`409` → "Ya tienes uno con ese nombre."), blank name ("Escribe un nombre."), rename with an expense already attached, removal while in use, create-inline mid-draft, unknown id (`unknown_id`), and creating an expense against an **archived** id via the API (defect D7).
- **Voice.** Cancel during recording; abandon during transcription; the 30-second auto-stop; a transcript with nothing usable in it; a transcript with no amount; a transcript with two competing amounts; permission denied at the browser level; a spoken question.
- **Insights.** Two questions at once (`409 busy`, honouring A22); cancel mid-flight; leave the screen mid-flight and return (job re-attached); a question about a category that does not exist; a question about a journal topic never written; an unresolvable period; an empty period; the model entirely down; the same journal question seven times to test grounding stability.
- **The arbiter.** Started a real voice capture while an insight question was generating: the question terminated `failed / preempted` at 6.1 s and the transcription finished in **6.34 s** — no slower than the 5.8 s uncontended baseline. Separately caught the scheduler's summary being preempted by an arriving transcription in normal operation.
- **Server lifecycle.** 9 restarts, one an ungraceful kill; a failed save mid-typing; cold recovery; a server started with a dead LLM; a server started with all outbound proxying broken; `LAN_BIND_ADDR=0.0.0.0` (correctly refused); both origins live at once.
- **Non-existent endpoints.** `/api/gym` → 404. `expenses.csv`, `journal.csv`, `export.csv` → 404. `GET /api/export?format=csv` returns **JSON** (the parameter is ignored, no CSV code path). **CSV was cut at the gate and does not exist. Confirmed.**
- **Pagination limits.** `?limit=500` → `400`; `?limit=200` honoured.

---

## Defects Found

**D1 — an undetermined amount or category is left empty but not marked as needing input (9.2, FAIL)**
1. Start a voice expense capture; have the transcript be "gasté cinco mil, no sé en qué".
2. On the review screen, MÉTODO DE PAGO carries a "FALTA ELEGIRLO" pill on a violet-tinted region. **CATEGORÍA carries no marker at all** and is visually identical to a satisfied field.
3. Repeat with "compré algo": **MONTO** is empty (showing a grey `$ 0` placeholder) with **no** marker.

Expected per 9.2: empty **and visibly marked as needing input**. Observed: empty, unmarked, for two of the three fields. Screenshots `57-voz-revision-sinCat.png`, `57-voz-revision-compreAlgo.png`.
*Related observation for PM, not a separate defect:* for "compré algo" the LLM assist filled CATEGORÍA with **Otros** (labelled *SUGERIDO*) for an utterance that names nothing. 9.3 sanctions suggesting a category, so I have not failed it — but whether "Otros" for "I bought something" is a suggestion or a default is PM's call, not mine.

**D2 — journal answers can assert things the user never recorded (11.1, FAIL)**
1. Record journal entries that mention groceries, a walk, a conversation with your mother.
2. Ask "¿qué me ha preocupado este mes?" repeatedly.
3. In **3 of 7** runs the answer appended a clause with no support in any entry: "…has estado reflexionando sobre tus **ingresos vs desembolsos semanales**" (income is not recorded by this app at all); "…e **Inversión en la inversión futura**"; "…el **miedo a perder dinero** en estos gastos semana tras semana".

The deterministic figure path is sound; this is the unguarded prose surface the design names. Reproducible by repetition, not by a single run — ask the same question several times.

**D3 — one empty month permanently hides the last real summary (11.15, FAIL)**
1. Use a database where June has expenses and July has none, with "now" in August.
2. Let the scheduler run. It writes **both** a `ready` June summary and an `empty` July row (log: `summary 2026-07 -> empty`, `summary 2026-06 -> ready`).
3. `GET /api/insights/summaries/latest` returns the July `empty` row.
4. Open `/finanzas/analisis`: "Julio de 2026 no tiene nada anotado." The June summary — which exists, is complete, and whose figures I verified against June's month view — is unreachable from the UI, and no endpoint lists summaries.

Expected per 11.15: the most recent **completed summary** is readable. Observed: it is not. `A0-resumen-oculto.png`.

**D4 — amounts inside generated summary prose are not in Colombian convention**
The July summary wrote "313.000 pesos" (correct); the June summary wrote "**346,000** pesos" (comma). Both come from the same prompt and the same model. The app's own formatter is never wrong; this is model prose the formatter does not touch. Flagged rather than failed: whether 2.5/constraint 21 reach LLM-generated text is PM's call.

**D5 — an absurd amount crashes the API with a leaked Python exception (server-side)**
```
POST /api/expenses {"amount_cop": 999999999999999999999, "category_id":1, "payment_method_id":1}
→ 500 {"error":{"code":"internal","message":"OverflowError: Python int too large to convert to SQLite INTEGER"}}
```
Expected: a `validation` rejection naming the field, as every other bad amount gets. Observed: an unhandled overflow and an English Python exception string in the envelope. **Not user-visible** — the UI rejects the value client-side and never renders `message` — so no criterion fails on it, but it is an unguarded input boundary.

**D6 — a 21-digit amount echoes as `1e.+21` in the field**
Type 21 digits into MONTO; the field displays `1e.+21` (the value passed through `Number` to `1e+21`, then the thousands formatter inserted a dot). Submitting is correctly refused in Spanish and nothing is saved, so this is cosmetic. `96-monto-absurdo.png`.

**D7 — the API still accepts an archived category for a new expense**
After archiving category 3 through the UI, `POST /api/expenses {"category_id":3,…}` returns **201**. The UI removes the chip so this is not reachable through the app, and 3.4's user-facing obligations all hold — but the server does not enforce "removed from future selection". Defence in depth only.

**D8 — a summary can state a figure that means nothing (11.2, FAIL)**
The July summary opens: "En julio de 2026, el usuario gastó un total de 313.000 pesos durante los días con algún gasto **(20)**." Nothing on the Finanzas screen is 20; July shows *3 gastos* across 3 days. `20` survives NumericGuard because it is a member of the fact set for an unrelated reason (the 20 July top-expense date) — the documented membership-not-meaning limit. Same root cause as D2: unguarded prose from a 3B local model. Every other figure in every summary and answer matched exactly.

---

## What I could not test, stated plainly

- **Spanish transcription accuracy (8.7, and the spoken half of 9.6/9.7).** No microphone, no Spanish TTS on this host. I did **not** synthesize audio and call it a pass. The parse layer is verified with text through the real backend; someone must still speak one Colombian Spanish sentence into a real microphone.
- **The live tailnet path (13.4).** Tailscale is installed but not logged in; that step is interactive and the human's. I verified the two-origin mechanism itself instead.
- **Literal internet severance (15.5).** No root, no sudo, no working `unshare`. I proved the equivalent property with `strace` and a broken-proxy run, and said so above rather than implying I pulled the cable.
