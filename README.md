# ui-refit

An Agent Skill that refreshes an existing UI's look without changing what it does. A
millwright doesn't scrap the machine; they refit it. Built by Millwright Labs.

Three modes, one philosophy:

- **Refit** — modernize an existing UI. Route slugs, form field names, analytics attributes,
  nav labels, and test selectors survive byte-for-byte, and the agent states its preserve
  list before the first edit.
- **Design** — new UI, forced through a plan → self-critique → build loop so the first draft
  isn't the same page every model produces for every brief.
- **Review** — read-only findings tagged P0/P1/P2 with `file:line`, a diagnosis before every
  fix, and a `PASS` verdict for clean code instead of invented problems.

Every mode ends with a runnable validator, not a vibe check.

## Install

```bash
git clone https://github.com/millwright-labs/ui-refit-skill ~/.claude/skills/ui-refit
```

Windows (PowerShell):

```powershell
git clone https://github.com/millwright-labs/ui-refit-skill "$env:USERPROFILE\.claude\skills\ui-refit"
```

That's the whole install. No build step, no dependencies — the validator is a single
standard-library Python file. Then ask Claude to "refresh this UI", "design a landing page",
or "review this page's UX".

## The validator

`scripts/validate_ui.py` pass/fails CSS and HTML on the checks that have real numbers behind
them: WCAG 2.2 contrast (with `var()` resolution and the large-text threshold), `transition:
all`, layout-property animation, removed focus outlines, missing reduced-motion guards,
off-grid spacing, type-scale sprawl, and known AI-default color families. Real output from
this repo's test fixture:

```
FAIL [contrast] evals/fixtures/dated-app/styles.css · body — color #999999 on background:#ffffff = 2.85:1, needs 4.5:1
FAIL [transition-all] evals/fixtures/dated-app/styles.css · .btn — transition: all 0.3s
FAIL [focus-visible] evals/fixtures/dated-app/styles.css · .btn — outline removed with no :focus-visible/:focus alternative in scope
WARN [reduced-motion] evals/fixtures/dated-app/styles.css · (file) — animation/transition present without a prefers-reduced-motion guard
WARN [spacing-grid] evals/fixtures/dated-app/styles.css · (file) — off-grid spacing values (not multiples of 4px): 3, 5, 7, 13, 18, 22px
RESULT: 3 FAIL, 2 WARN, 1 files checked
```

Exit 1 on any FAIL. When there's nothing checkable it says `ABSTAIN` instead of pretending
to pass. The skill treats a FAIL as unfinished work: fixed, or explicitly accepted by you.

## Why it exists

Before writing this skill we deep-read eleven UI/UX skills for Claude Code — the official
ones, the most-installed community ones, and the best-sourced ones we could find — and
pulled the judging numbers from primary sources (WCAG 2.2, Nielsen Norman Group, ISO
9241, Apple HIG, Material 3, web.dev, Practical Typography). Full writeup:
[docs/RESEARCH.md](docs/RESEARCH.md). The short version — generation-time taste, review-time
rigor, and a validator that can fail you never lived in one skill, and none of them promised
to leave your routes, form names, and analytics alone. This one is built around exactly
those gaps.

Honest comparison with the skills we learned the most from:

| Skill | What it does better | What ui-refit adds |
|---|---|---|
| frontend-design (Anthropic) | The original plan-then-critique loop, leaner file | Preserve-by-default refits, checkable numbers, the validator, a review mode |
| Web Interface Guidelines (Vercel) | Broader rule catalog (~100 rules), maintained by Vercel | Rules pinned locally with numbers and sources; generation guidance, not only auditing |
| ui-ux-pro-max | Breadth on demand: 88 styles, 192 palettes via search | Curated judgment over enumerated volume; a gate that stops unrequested redesigns |

## Tested behavior

Ten behavioral eval cases, run against fresh agents with artifact-level verification (diffs
and greps, not self-reports): the no-redesign gate holds, every preserve string checks out
intact after a refit, supplied brand tokens stay locked, reviews invent nothing on clean code, and
the plan-critique step demonstrably fires before the first edit. The gate also held on
GPT-5.2 and Gemini. Full run, including the two validator bugs the evals caught and fixed:
[evals/RESULTS.md](evals/RESULTS.md).

## Known limits

- The validator reads stylesheets, not rendered pages: no computed cascade, no layout checks
  (target sizes), one level of `var()` resolution, no CSS-in-JS.
- `references/anti-defaults.md` describes what generated design collapses into as of
  2026-08-19. Model defaults drift; the file carries its review date and gets re-checked
  quarterly. An explicit request for any listed look always wins.
- Small models are unverified with this skill. Evals ran on Claude (plus gate-case checks on
  GPT-5.2 and Gemini); one run per case, which demonstrates the mechanism but doesn't
  measure variance.

## Sources

The numbers in `SKILL.md` and `references/` cite WCAG 2.2 success criteria, Apple HIG,
Material 3, web.dev Core Web Vitals, and Butterick's Practical Typography inline. Several
review rules are adapted from Vercel's
[Web Interface Guidelines](https://github.com/vercel-labs/web-interface-guidelines) (MIT),
tagged (WIG) where used.

MIT © 2026 Millwright Labs
