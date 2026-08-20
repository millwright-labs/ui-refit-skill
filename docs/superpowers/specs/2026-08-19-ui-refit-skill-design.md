# ui-refit — design spec (2026-08-19)

Second public Millwright Labs Agent Skill (after minto-pyramid-skill). An Agent Skill that
refreshes existing UIs without rewriting them, generates new UI with the same discipline, and
reviews UI code with prioritized findings — built on the 2026-08-19 research pass over the top
UI/UX skills and primary-source design metrics (see `docs/RESEARCH.md` in this repo;
internal pointer: shared-memory/ui-ux-skill-research.md, artifact 82d6b1b1).

## Decisions already made (user-approved)

- Name **ui-refit**; repo `millwright-labs/ui-refit-skill`; public + MIT at ship, per the
  established Millwright publishing pattern (SKILL.md at repo root, clone-and-go, no build step).
- v1 ships **all three modes** and the **Python validator**.
- GitHub page = rich README + full research writeup at `docs/RESEARCH.md`.
- Production quality bar: eval suite + external cross-check (Codex AND Gemini) before the repo
  goes public.

## The one-sentence thesis

A millwright doesn't scrap the machine — they refit it. The skill's identity is
**preserve-by-default modernization**: everything that works is kept; what changed is listed;
every claim about quality is either a checkable number or an explicit judgment call.

## Architecture

```
ui-refit-skill/                      (repo root == installable skill dir)
├── SKILL.md                         router + shared foundations (~150 lines)
├── references/
│   ├── refit-playbook.md            maturity tiers, preserve/replace lists, theming contract
│   ├── review-rules.md              MUST/SHOULD/NEVER ruleset + P0/P1/P2 output format
│   └── anti-defaults.md             date-stamped cliché list + official-package routing table
├── scripts/
│   ├── validate_ui.py               stdlib-only pass/fail validator
│   └── test_validate_ui.py          fixture-based self-test (assert-style, runnable directly)
├── evals/
│   ├── cases.json                   behavioral assertions (Anthropic eval structure, as minto)
│   ├── fixtures/                    small HTML/CSS apps the cases run against
│   └── RESULTS.md                   honest per-model results
├── docs/RESEARCH.md                 the public research writeup (no personal attribution)
├── README.md                        pitch, install, evidence story, comparison, limits
├── LICENSE                          MIT, Millwright Labs
└── .gitattributes                   * text=auto eol=lf
```

Skill runtime never reads `evals/`, `docs/`, `README.md` — they ride along in the clone but cost
zero tokens. Progressive disclosure: SKILL.md alone handles trivial cases via an embedded
numbers table; each mode loads at most one reference file; the validator is run, never read.

## SKILL.md design

**Frontmatter description** leads with what it does, then when to use it (Anthropic
skill-authoring guidance governs the matcher; this deliberately contradicts
superpowers:writing-skills — same call as minto). Triggers to cover: refresh / modernize /
freshen / update the look / redesign / "make it look current", UI review / design audit, and
new-page/app UI design. Refit and Review wording is claimed strongly; Design wording moderately
(the official frontend-design skill also matches generation requests — coexistence is fine,
collision documented in README).

**Step 0 gate (minto's hardest-won lesson, restated as a positive contract):** classify the
request before doing anything. If the user shared UI code but did not ask for design changes,
the response is an answer to their actual question, plus at most a two-sentence observation
naming the biggest design issue and offering the refit — the response's shape is
answer-then-offer, never unrequested redesign. Prohibitions lose to helpfulness pull; the rule
states what the output IS.

**Mode router:** pick Refit (existing UI, changes wanted), Design (new UI), or Review
(assessment only, no edits). Ambiguous → choose, announce in one line, proceed; the user can
redirect. (oiloil's pattern.)

**Shared foundations (all modes):**
- Precedence: user's words → the project's existing design system (tokens, theme files,
  component conventions — read them first) → this skill's opinions.
- The numbers quick-table (from bucket C of the research): contrast 4.5:1 / 3:1 large / 3:1 UI
  components; targets ≥24 CSS px (44pt/48dp touch); body 15–25px w/ 16px mobile floor;
  line length 45–90ch (~65ch); line-height 1.4–1.6 body / ~1.2 headings; spacing on a
  4/8px scale; never `transition: all`; never animate top/left/width/height; visible focus
  always; `prefers-reduced-motion` honored. Each row cites its source (WCAG 2.2 SC numbers,
  Apple HIG, M3, Butterick).
- Quality floor as a positive contract: ships responsive, keyboard-navigable, with visible
  focus, defined loading/empty/error states where interaction exists.

**Refit mode (flagship):**
1. Silent scan: framework, styling method, tokens/theme, component conventions, real pages.
2. Tier the project (blank / half-built / mature / messy-legacy / uncertain) — each tier has a
   scripted opening move, so the user gets one calibrated question, not ten.
3. Audit against the numbers table + anti-defaults list → what's dated, what's broken, what's fine.
4. Write the preserve list (tech stack, behavior, route slugs, form field names, analytics
   events/IDs, nav labels, test selectors) and the replace list. Preserve list is stated to the
   user before any edit.
5. Refit plan: token-level changes (color/type/spacing/radius/shadow/motion) + one Signature
   element, then self-critique — any part that reads like the generic default for "modernize
   this" gets revised, with the change named.
6. Implement incrementally; behavior-testing after each slice; run the validator; end with
   before/after evidence (screenshot when a browser is available).

**Design mode:** two-pass plan (Color as 4–6 named hex values / Type roles / Layout / Signature)
→ self-critique against the generic default → build → validator → quality floor check.

**Review mode:** load `review-rules.md`; findings as P0 (task-breaking) / P1 (friction) /
P2 (polish) with `file:line`; every P0/P1 carries a one-line diagnosis (can't find how = execution
gulf; can't tell what happened = evaluation gulf) before its fix; zero edits in this mode; a clean
file gets "pass", not invented findings.

## references/ design

**refit-playbook.md (~100 lines):** the five tiers with opening moves; preserve/replace lists in
full; incremental discipline; the three-state theming contract generalized for real apps (tokens
on `:root`, dark via `prefers-color-scheme`, explicit `[data-theme]` override where the app
supports a toggle; every color reachable in the un-stamped state).

**review-rules.md (~180 lines):** MUST/SHOULD/NEVER rules across focus & keyboard, targets &
forms, animation, layout & responsiveness, color & contrast, states & feedback, copy, dark mode,
performance. Authored in our own words from primary sources (WCAG 2.2, NN/g, Apple HIG, M3,
web.dev) with Vercel's Web Interface Guidelines credited as prior art. **License check is a build
task:** if Vercel WIG is MIT/CC-compatible, a subset may be adapted with attribution; otherwise
all rules are original phrasings of the underlying (uncopyrightable) facts. Either way the file
pins a local copy — no runtime fetch (the fork/drift failure found in Vercel's own skill).

**anti-defaults.md (~80 lines):** header states "Observations of current-generation model
defaults, reviewed 2026-08-19 — re-verify quarterly; these are calibration data, not law, and a
brief that explicitly asks for one of these looks wins." The named clusters (cream + serif
display + terracotta; near-black + lone acid accent; broadsheet hairlines; purple→blue gradient
hero; Inter/Space Grotesk as the reflex face; emoji as section markers; uniform rounded-lg;
three equal feature cards; glassmorphism everywhere), each described in our own words. Plus the
official-package routing table: a brief that reads as Material / Fluent / Carbon / GOV.UK /
USWDS / shadcn → install the real package, never hand-fake its CSS.

## Validator design (scripts/validate_ui.py)

Stdlib-only, Windows-safe (UTF-8 stdout forced, pathlib, no shell-outs). Input: one or more CSS/
HTML file paths or a directory (globs *.css, *.html; reads `<style>` blocks). Single-file, no deps.

Checks and severities:

| Check | Severity | Detail |
|---|---|---|
| Contrast on resolved color pairs | FAIL < 4.5:1 (WARN if likely large text) | Rules declaring both color and background(-color); `var()` resolved one level against `:root`/`[data-theme]` blocks; hex/rgb()/named-subset only |
| `transition: all` | FAIL | exact property match |
| Layout props in transition/animation | FAIL | top/left/width/height in transition-property or keyframes |
| `outline: none/0` without any `:focus-visible` styling in scope | FAIL | file-scope check |
| Animations present but no `prefers-reduced-motion` guard | WARN | |
| Spacing off a 4px grid | WARN | margin/padding/gap px values; reports the offenders and the inferred scale |
| Distinct font-size count > 8 | WARN | type-scale discipline proxy |
| Anti-default cliché hex families | WARN | embedded date-stamped list, mirrors anti-defaults.md |

Exit code 0 = no FAILs (WARNs listed); 1 = at least one FAIL; 0 with an explicit
"nothing checkable found — validator abstains" line when no CSS resolves (abstain ≠ pass ≠ fail,
stated honestly; never silent). Out of scope, documented in the script header: computed-style
cascade, target sizes (needs layout), cross-file token resolution beyond one level, CSS-in-JS.

`test_validate_ui.py`: fixture strings covering each check firing AND each check staying silent
on the correct form (control cases — the failure-guard lesson), plus the abstain path. Plain
asserts, `python scripts/test_validate_ui.py` exits 0/1.

## Evals design (evals/)

minto's structure: cases.json + fixtures/ + RESULTS.md. ~10 cases; the load-bearing ones:

1. **Gate holds:** user shares UI code asking a functional question → answer + two-sentence
   offer max, zero redesign. (The case minto failed on v1 — written as shape-of-output assertion.)
2. **Refit preserves:** fixture app with dated look + named route slugs/form fields/analytics
   IDs → refit output changes none of them, and states its preserve list first.
3. **Plan-then-critique visible:** refit/design output contains the token plan and an explicit
   revision note before code.
4. **No cliché landing (Design mode):** greenfield finance-app brief → palette avoids the named
   cluster hexes unless asked.
5. **Brand lock:** supplied brand color/typeface carried verbatim, not re-litigated.
6. **Existing-system respect:** fixture with a tokens.css → refit modifies tokens, doesn't
   introduce a parallel palette.
7. **Review is read-only:** review mode emits P0/P1/P2 with file:line and changes no files.
8. **Review doesn't invent:** clean fixture → pass verdict, no fabricated findings.
9. **Validator invoked:** refit/design run ends with validator execution and honest reporting
   of its output (including a deliberate WARN fixture).
10. **Ambiguity handling:** "make this better" → mode announced in one line, then proceeds.

Models: session model + Sonnet as primary; GPT-5 and Gemini via the codex / model-bridge lanes
for portability (minto precedent); Haiku tested and documented as unsupported if it fails the gate.

## README design

Sections: what it is (three modes, one philosophy) · install one-liners (git clone to
`~/.claude/skills/ui-refit`, plus Windows PowerShell variant) · why it's different (the evidence
story: built from a structured review of 10 UI/UX skills + primary-source metrics, linking
docs/RESEARCH.md) · the validator (sample output) · comparison table vs. frontend-design /
Vercel WIG / ui-ux-pro-max (honest: what each does better) · eval results · known limits
(Haiku if applicable, validator scope, anti-defaults staleness + quarterly review promise) ·
provenance & sources · MIT. Written under the humanize-copy gate. No personal/Barron attribution
anywhere (Millwright publishing rule).

## Risks (premortem, condensed)

- **Brand risk (skill is mediocre under the Millwright name):** eval gate + Codex AND Gemini
  cross-checks before the public flip; RESULTS.md publishes failures honestly.
- **License risk:** verify Vercel WIG + anthropics/skills licenses before adapting any text;
  default to original phrasing + attribution. No verbatim lifts without a compatible license.
- **Staleness:** anti-defaults list decays by design — date-stamp + quarterly review note in
  README; validator mirrors the same list with the same stamp.
- **Trigger overlap with installed frontend-design plugin:** documented in README ("pairs with");
  locally Daniel keeps ui-refit and can drop the official one — his call at install time, and
  the skill descriptions are worded to divide territory (refresh/review vs. blank-page).
- **Validator false positives → users tune it out:** FAIL tier reserved for unambiguous defects;
  everything judgment-flavored is WARN; abstain path is explicit. Control cases in the test file.
- **Haiku misbehavior:** evals will tell; documented unsupported if so (minto precedent).

## Build order

1. Scaffold (LICENSE, .gitattributes, dirs) → commit.
2. `validate_ui.py` + tests green → commit.
3. references/ (three files) → commit.
4. SKILL.md (under superpowers:writing-skills + writing-for-agents) → commit.
5. Local install to `~/.claude/skills/ui-refit` + smoke test.
6. Evals: fixtures, cases, run vs session model + Sonnet (+ GPT-5/Gemini lanes), iterate until
   the gate/preserve cases hold → RESULTS.md → commit.
7. docs/RESEARCH.md + README (humanize-copy gate) → commit.
8. External cross-check: Codex AND Gemini review of the whole repo; triage findings → commit.
9. Secrets audit → push → flip public → topics set → update memory state doc.
