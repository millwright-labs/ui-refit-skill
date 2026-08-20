# ui-refit Skill Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ship `millwright-labs/ui-refit-skill` — a three-mode Agent Skill (Refit / Design / Review) with a stdlib Python validator, behavioral eval suite, research writeup, and production README.

**Architecture:** Repo root doubles as the installable skill dir (clone-and-go). SKILL.md routes to one of three modes; each mode loads at most one file from `references/`; `scripts/validate_ui.py` is executed, never read. `evals/` and `docs/` ride along at zero runtime token cost.

**Tech Stack:** Markdown (skill + references), Python 3 stdlib only (validator), JSON (evals). No dependencies, no build step.

**Spec:** `docs/superpowers/specs/2026-08-19-ui-refit-skill-design.md`

## Global Constraints

- Python: stdlib only; force UTF-8 stdout (`sys.stdout.reconfigure(encoding="utf-8")`); `pathlib` for all paths; must run on Windows and POSIX.
- All behavioral rules in SKILL.md are written as positive contracts (what the output IS), never prohibitions — minto lesson.
- Frontmatter description leads with what the skill does, then when to use it.
- No verbatim text from other skills unless its license is verified compatible; primary-source facts restated in original words with citations.
- No personal or Barron attribution anywhere in the repo — Millwright Labs only.
- Multi-line git commit messages via `git commit -F <file>` (file written with the Write tool first), never inline `-m`.
- Line endings: `.gitattributes` normalizes to LF.
- Token budgets: SKILL.md ≤ ~160 lines; each reference file ≤ ~190 lines.

---

### Task 1: Scaffold

**Files:**
- Create: `.gitattributes`, `.gitignore`, `LICENSE`

**Interfaces:** Produces the repo skeleton later tasks write into.

- [ ] **Step 1:** `.gitattributes` containing exactly:

```
* text=auto eol=lf
```

- [ ] **Step 2:** `.gitignore` containing:

```
__pycache__/
*.pyc
```

- [ ] **Step 3:** `LICENSE` — MIT, `Copyright (c) 2026 Millwright Labs`.
- [ ] **Step 4:** Commit: `chore: scaffold repo (license, line endings)`.

---

### Task 2: Validator (`scripts/validate_ui.py` + `scripts/test_validate_ui.py`)

**Files:**
- Create: `scripts/validate_ui.py`, `scripts/test_validate_ui.py`

**Interfaces:**
- Produces CLI: `python scripts/validate_ui.py <path> [<path>...]` where path = .css/.html file or directory (recurses, globs `*.css`, `*.html`; HTML contributes its `<style>` block contents).
- Exit 0 = no FAILs; exit 1 = ≥1 FAIL. When nothing checkable is found, print `ABSTAIN: no checkable CSS found` and exit 0.
- Output lines: `FAIL [check-id] <file> · <selector> — <detail>` / `WARN [...]` then a summary line `RESULT: <n> FAIL, <n> WARN, <n> files checked`.

**Checks (check-id → logic):**

| id | severity | logic |
|---|---|---|
| `contrast` | FAIL (<4.5:1; 3:1 when same rule has font-size ≥24px, or ≥18.66px with font-weight ≥700) | For each rule declaring BOTH `color` and `background`/`background-color`: resolve `var(--x)` one level against custom props collected from `:root` / `[data-theme]` / `html` / `body` blocks (ambiguous multi-definition vars: skip pair unless all definitions equal); parse `#rgb`/`#rrggbb`/`rgb()`/`rgba()`/named subset (black, white, red, green, blue, gray, grey, silver, orange, yellow, purple, navy, teal, transparent); any alpha < 1 or unparsable → skip pair. Ratio = WCAG relative luminance formula. |
| `transition-all` | FAIL | `transition` or `transition-property` value containing word `all`. |
| `layout-anim` | FAIL | `transition`/`transition-property` shorthand naming `top`, `left`, `right`, `bottom`, `width`, `height` (word-bounded, so `min-width` in a `width` check must NOT match — use `\b(top|left|right|bottom|width|height)\b` after splitting on commas and taking each first token); or a `@keyframes` block declaring any of those properties. |
| `focus-visible` | FAIL | Any rule sets `outline: none` or `outline: 0` AND no selector in the scanned set contains `:focus-visible` or `:focus` with a non-none `outline` or any `box-shadow`. |
| `reduced-motion` | WARN | `animation` or `transition` declarations exist anywhere AND the raw text contains no `prefers-reduced-motion`. |
| `spacing-grid` | WARN | px values in `margin*`, `padding*`, `gap`, `row-gap`, `column-gap`: value is off-grid when `v > 2 and v % 4 != 0`. Report distinct offenders. |
| `type-scale` | WARN | > 8 distinct px `font-size` values across scanned files. |
| `cliche-color` | WARN | Any parsed color within Euclidean RGB distance 16 of: `#F4F1EA`, `#F5F1EA` (AI-default cream), `#8B5CF6`, `#7C3AED`, `#6366F1`, `#A855F7` (AI-default purple/violet gradient family). Message points to `references/anti-defaults.md` and states these are legitimate when deliberately chosen. |

Parsing approach: strip `/* */` comments; walk the text with a small brace-depth state machine that records `@media`/`@keyframes` context strings; inside depth-1 (or depth-2 under a media query) blocks split declarations on `;` then first `:`. No external parser. Selector reported as written. HTML files: extract `<style>...</style>` contents via regex, then same pipeline; inline `style=""` attributes are out of scope (documented in module docstring along with: computed-cascade, layout-dependent checks like target size, cross-file var chains beyond one level, CSS-in-JS).

- [ ] **Step 1: Write the failing tests** — `scripts/test_validate_ui.py`, plain asserts, no framework. One fire case AND one control case per check, plus abstain. Core shape:

```python
import subprocess, sys, tempfile
from pathlib import Path
import validate_ui as v

def run(css: str):
    return v.validate_text(css, "test.css")   # returns list of Finding(severity, check_id, where, detail)

def ids(findings, sev=None):
    return [f.check_id for f in findings if sev is None or f.severity == sev]

# contrast
assert "contrast" in ids(run(".a{color:#777;background:#888;}"), "FAIL")
assert "contrast" not in ids(run(".a{color:#111;background:#fff;}"))
# var resolution, one level
assert "contrast" in ids(run(":root{--fg:#777;--bg:#888;} .a{color:var(--fg);background:var(--bg);}"), "FAIL")
# large text threshold: #8A8A8A on #fff ~= 3.45:1 -> passes at >=24px, FAILs at body size
assert "contrast" not in ids(run(".h{color:#8A8A8A;background:#fff;font-size:32px;}"), "FAIL")
assert "contrast" in ids(run(".p{color:#8A8A8A;background:#fff;}"), "FAIL")
# alpha -> skip (no finding either way)
assert "contrast" not in ids(run(".a{color:rgba(0,0,0,.5);background:#fff;}"))
# transition-all
assert "transition-all" in ids(run(".a{transition: all .2s;}"), "FAIL")
assert "transition-all" not in ids(run(".a{transition: opacity .2s, transform .2s;}"))
# layout-anim
assert "layout-anim" in ids(run(".a{transition: width .3s;}"), "FAIL")
assert "layout-anim" not in ids(run(".a{transition: min-width .3s;}"))   # control: word boundary
assert "layout-anim" in ids(run("@keyframes slide{from{left:0}to{left:100px}}"), "FAIL")
# focus-visible
assert "focus-visible" in ids(run("button{outline:none;}"), "FAIL")
assert "focus-visible" not in ids(run("button{outline:none;} button:focus-visible{outline:2px solid #000;}"))
# reduced-motion
assert "reduced-motion" in ids(run(".a{animation: spin 1s linear infinite;}"), "WARN")
assert "reduced-motion" not in ids(run(".a{animation: spin 1s;} @media (prefers-reduced-motion: reduce){.a{animation:none;}}"))
# spacing-grid
assert "spacing-grid" in ids(run(".a{padding: 13px;}"), "WARN")
assert "spacing-grid" not in ids(run(".a{padding: 16px 8px; margin: 2px;}"))
# type-scale: 9 distinct sizes fires, 3 doesn't
many = "".join(f".s{i}{{font-size:{10+i}px;}}" for i in range(9))
assert "type-scale" in ids(run(many), "WARN")
assert "type-scale" not in ids(run(".a{font-size:16px;}.b{font-size:20px;}"))
# cliche-color
assert "cliche-color" in ids(run(".hero{background:#8B5CF6;}"), "WARN")
assert "cliche-color" not in ids(run(".hero{background:#0E6B5C;}"))
# abstain: unparsable/no css
assert v.validate_text("<p>no styles here</p>", "x.html") == [] 
# CLI exit codes via subprocess on temp files
with tempfile.TemporaryDirectory() as d:
    bad = Path(d, "bad.css"); bad.write_text(".a{transition:all .2s}", encoding="utf-8")
    ok  = Path(d, "ok.css");  ok.write_text(".a{color:#111;background:#fff}", encoding="utf-8")
    assert subprocess.run([sys.executable, "scripts/validate_ui.py", str(bad)]).returncode == 1
    assert subprocess.run([sys.executable, "scripts/validate_ui.py", str(ok)]).returncode == 0
print("all validator tests passed")
```

- [ ] **Step 2:** Run `python scripts/test_validate_ui.py` → expect ImportError/AssertionError (no implementation yet).
- [ ] **Step 3:** Implement `validate_ui.py`: module docstring (scope + out-of-scope list), `Finding` namedtuple `(severity, check_id, where, detail)`, `parse_css(text) -> (rules, custom_props, raw)` state machine, `relative_luminance(rgb)` and `contrast_ratio(a, b)` per WCAG (`L = 0.2126R + 0.7152G + 0.0722B` with the ≤0.04045 linearization branch), `validate_text(text, name) -> list[Finding]` running all eight checks, `main(argv)` handling files/dirs/HTML extraction, output lines, ABSTAIN path, exit code. Windows note: first lines force UTF-8 stdout.
- [ ] **Step 4:** Run `python scripts/test_validate_ui.py` → `all validator tests passed`.
- [ ] **Step 5:** Commit: `feat: add stdlib UI validator with fire+control test suite`.

---

### Task 3: `references/refit-playbook.md`

**Files:** Create: `references/refit-playbook.md` (≤190 lines)

**Interfaces:** Loaded by SKILL.md's Refit mode. Section names consumed verbatim by SKILL.md: `## Tier the project`, `## The preserve list`, `## The replace list`, `## Incremental discipline`, `## Theming contract`.

- [ ] **Step 1:** Author with this content contract:
  - Tiers: blank / half-built / mature / messy-legacy / uncertain — each with a one-line detection cue and a scripted opening move (e.g. mature → "propose token-level changes only, list what stays").
  - Preserve list (stated to the user before any edit): tech stack & styling method, runtime behavior, route slugs & URL params, form field names & IDs, analytics events/attributes, nav labels, test selectors (`data-testid` etc.).
  - Replace list targets: dated visual tokens, missing interaction states, off-scale spacing, cliché patterns (pointer to anti-defaults.md), weak hierarchy.
  - Incremental discipline: one slice → behavior check → next; the refit ends with a what-changed/what-stayed summary and validator output.
  - Theming contract: tokens defined on `:root`; dark palette via `@media (prefers-color-scheme: dark)`; explicit `[data-theme]` overrides win over the media query when the app has a toggle; every color must resolve in the un-stamped state; body background always painted from a token.
- [ ] **Step 2:** Commit: `feat: add refit playbook reference`.

---

### Task 4: `references/review-rules.md`

**Files:** Create: `references/review-rules.md` (≤190 lines)

**Interfaces:** Loaded by Review mode. Defines the output format SKILL.md promises: P0/P1/P2 with `file:line`, diagnosis line, fix, and the closing verification checklist.

- [ ] **Step 1:** License check: fetch `https://github.com/vercel-labs/web-interface-guidelines` LICENSE via `gh api repos/vercel-labs/web-interface-guidelines/license --jq .license.spdx_id`. Record result in the commit message. MIT/Apache/CC-BY → adapting short rule phrasings with attribution is allowed; anything else (or no license) → original phrasing only, credited as prior art.
- [ ] **Step 2:** Author ~60–80 rules as `MUST:` / `SHOULD:` / `NEVER:` bullets grouped: Focus & keyboard · Targets & forms · States & feedback · Animation · Layout & responsiveness · Color & contrast · Typography · Copy · Dark mode · Performance. Every numeric rule carries its number and source tag (WCAG SC, HIG, M3, web.dev, Butterick). Include the review output contract: findings grouped by file, `path:line`, each P0/P1 opens with a one-line diagnosis (execution gulf = can't find how; evaluation gulf = can't tell what happened), each finding ends with a concrete fix; a clean target gets `PASS` and nothing invented.
- [ ] **Step 3:** Commit: `feat: add review ruleset (license check: <result>)`.

---

### Task 5: `references/anti-defaults.md`

**Files:** Create: `references/anti-defaults.md` (≤120 lines)

**Interfaces:** Loaded by Refit/Design when choosing aesthetics; hex list mirrored in `validate_ui.py` `cliche-color`.

- [ ] **Step 1:** Author: header block stating these are observations of current-generation model defaults, **Reviewed: 2026-08-19**, re-verify quarterly, calibration data not law, an explicit user request for any of these wins. Clusters, each in original words with its tell-tale signs: cream + display serif + terracotta; near-black + single acid accent; broadsheet hairlines; purple→violet gradient hero; reflex-Inter/Space-Grotesk; emoji as section markers; uniform large border-radius on everything; three equal feature cards; glassmorphism everywhere. Then the official-package routing table: brief reads as Material / Fluent / Carbon / GOV.UK / USWDS / shadcn → install and use the real package. Close with the positive move: derive distinctiveness from the subject's own world + one Signature element.
- [ ] **Step 2:** Commit: `feat: add date-stamped anti-defaults reference`.

---

### Task 6: `SKILL.md`

**Files:** Create: `SKILL.md` (≤160 lines)

**Interfaces:** Consumes section names from Tasks 3–5 and the validator CLI from Task 2, all referenced by exact path.

- [ ] **Step 1:** Invoke `superpowers:writing-skills` and `writing-for-agents`; author to the spec's SKILL.md design:
  - Frontmatter: `name: ui-refit`; description leading with what it does, then when: refreshing/modernizing an existing UI's look, designing new UI, or reviewing UI code — with the trigger nouns (refresh, modernize, redesign, "look dated", UI review/audit, design a page/app).
  - Step 0 gate as a positive contract (answer-then-offer shape when design changes weren't requested).
  - Mode router (Refit default when an existing UI + change intent; Design when nothing exists; Review when assessment only; ambiguous → announce choice in one line, proceed).
  - Shared foundations: precedence chain; the numbers quick-table with source tags; quality-floor contract.
  - Per-mode process blocks exactly as spec'd, each naming its reference file path and when to run `python scripts/validate_ui.py <targets>` relative to the skill dir.
- [ ] **Step 2:** Self-check against `writing-for-agents` (routing clarity, no dead references, budget ≤160 lines) and fix inline.
- [ ] **Step 3:** Commit: `feat: add ui-refit SKILL.md router`.

---

### Task 7: Local install + smoke test

**Files:** none in repo (copies repo → `~/.claude/skills/ui-refit`)

- [ ] **Step 1:** `robocopy` (PowerShell) or `cp -r` (Bash) repo → `C:\Users\Daniel\.claude\skills\ui-refit`, excluding `.git`, `docs/superpowers`. Do NOT try to git-commit anything under `~/.claude` (skills/ is gitignored there by design).
- [ ] **Step 2:** Smoke: `python C:/Users/Daniel/.claude/skills/ui-refit/scripts/validate_ui.py evals/fixtures` runs (after Task 8 fixtures exist, rerun); confirm SKILL.md frontmatter parses (name+description present, no tabs).

---

### Task 8: Evals

**Files:**
- Create: `evals/fixtures/dated-app/index.html`, `evals/fixtures/dated-app/styles.css`, `evals/fixtures/clean-app/index.html`, `evals/fixtures/tokens-app/index.html`, `evals/fixtures/tokens-app/tokens.css`, `evals/cases.json`, `evals/RESULTS.md`

**Interfaces:** cases.json entries: `{id, name, mode_expected, prompt, files[], assertions:[{kind: "behavior"|"artifact", text}]}` (minto/oiloil shape).

- [ ] **Step 1:** Fixtures. `dated-app`: small "job tracker" page with a 2012-era look (gradient buttons, 12px text, `transition: all`, off-grid padding) AND preservation hooks: links `/jobs?filter=open`, `<form>` fields `name="customer_email"`, `data-analytics="submit-job"`, nav labels, `data-testid="job-row"`. `clean-app`: genuinely fine small page (passes validator, no clichés). `tokens-app`: page styled entirely via `tokens.css` custom properties.
- [ ] **Step 2:** `cases.json` — the 10 cases from the spec (gate-holds; refit-preserves; plan-then-critique-visible; no-cliché-landing; brand-lock; existing-system-respect; review-read-only; review-no-invention; validator-invoked-and-reported; ambiguity-one-line). Each prompt written verbatim; each assertion checkable by reading the transcript/output.
- [ ] **Step 3:** Run each case in a FRESH subagent (session model; re-run the four cheapest on Sonnet) pointed at the installed skill copy + fixture paths, one case per agent, transcript judged against assertions by the session model. Iterate SKILL.md/references until the gate and preserve cases hold; every edit re-syncs the local install (Task 7 Step 1).
- [ ] **Step 4:** GPT-5 (codex MCP) and Gemini (model-bridge) portability spot-run of the gate case + one refit case. Record everything in `RESULTS.md` honestly (model, date, pass/fail per assertion, notable failures verbatim).
- [ ] **Step 5:** Commit: `test: add behavioral eval suite with fixtures and results`.

---

### Task 9: `docs/RESEARCH.md`

**Files:** Create: `docs/RESEARCH.md`

- [ ] **Step 1:** Adapt the 2026-08-19 field-guide content for public consumption as Millwright Labs research notes: the four skill archetypes, per-skill findings (factual, fair, no dunking — named repos get accurate descriptions), the four-bucket judging framework with the full numbers tables and primary-source citations, cross-cutting lessons, and how each finding shaped ui-refit. No personal names, no internal paths, no artifact links.
- [ ] **Step 2:** Commit: `docs: add the research behind ui-refit`.

---

### Task 10: `README.md`

**Files:** Create: `README.md`

- [ ] **Step 1:** Invoke `humanize-copy` FIRST (public-facing prose; loop its eval gate until green). Sections: what it is (three modes, preserve-by-default thesis) · install (`git clone https://github.com/millwright-labs/ui-refit-skill ~/.claude/skills/ui-refit` + PowerShell variant) · why it's different (evidence story linking docs/RESEARCH.md) · validator with real sample output from the dated-app fixture · honest comparison table (frontend-design, Web Interface Guidelines, ui-ux-pro-max — what each does better) · eval results summary linking RESULTS.md · known limits (validator scope, anti-defaults staleness + quarterly review, unsupported models if any) · sources · MIT.
- [ ] **Step 2:** Commit: `docs: add README`.

---

### Task 11: External cross-check (mandatory pre-ship)

- [ ] **Step 1:** Codex (mcp__codex__codex, read-only) review of the full repo: correctness of validator logic + WCAG math, SKILL.md contradiction hunt, README accuracy. Bounded prompt, <25 min.
- [ ] **Step 2:** Gemini (model-bridge `codegen`, smol :8892) same charter, independent.
- [ ] **Step 3:** Triage findings (session model judges); fix what's real; note rejections with reasons. Commit: `fix: address external review findings`.

---

### Task 12: Ship

- [ ] **Step 1:** Secrets audit: `git grep -iE "(api[_-]?key|token|password|secret|ghp_|sk-)" -- . ':!docs/superpowers'` → expect zero real hits (rule-name mentions in prose are fine — read every hit).
- [ ] **Step 2:** Push: `git push -u origin main` (plain git, not gh — known trap). Verify with `gh repo view millwright-labs/ui-refit-skill --json pushedAt`.
- [ ] **Step 3:** Flip public: `gh repo edit millwright-labs/ui-refit-skill --visibility public --accept-visibility-change-consequences`. Set topics: `claude`, `claude-code`, `agent-skills`, `ui`, `ux`, `design`, `frontend`.
- [ ] **Step 4:** Update `shared-memory/ui-ux-skill-research.md` (status → shipped, repo link) and create `shared-memory/ui-refit-skill-state.md` with repo/stage frontmatter (`stage: testing`). Final report to Daniel with repo URL.
