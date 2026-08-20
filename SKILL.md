---
name: ui-refit
description: Refreshes an existing UI's look without changing its behavior, designs new UI with the same discipline, and reviews UI code against evidence-based rules backed by a runnable validator. Use when a UI looks dated or needs a refresh/modernization/redesign, when designing a new page, app, or component UI, or when asked to review or audit UI, UX, accessibility, or visual design quality.
---

# ui-refit

A millwright doesn't scrap the machine — they refit it. This skill modernizes the look while
everything that works keeps working, and every quality claim is either a checkable number or
a named judgment call.

## Step 0 — read the request

Classify before acting. When the user shared UI code but asked about something else (a bug,
a question, other work), the response is: the answer to what they asked, then at most two
sentences naming the single biggest design issue observed and offering a refit. Design work
begins when they say yes or asked for it in the first place. When they did ask for design
work, pick the mode:

| Mode | When | Reference to load |
|---|---|---|
| **Refit** (default) | An existing UI + intent to change how it looks | `references/refit-playbook.md` |
| **Design** | No existing UI to change | `references/anti-defaults.md` |
| **Review** | Assessment wanted, no edits | `references/review-rules.md` |

Ambiguous requests ("make this better"): choose the closest mode, announce the choice in one
line, and proceed — the user redirects if you guessed wrong.

## Foundations — every mode

**Precedence:** the user's words → the project's existing design system (tokens, theme files,
component conventions — read them before proposing anything) → this skill's opinions.

**The numbers.** Quality claims resolve against these, each with its source:

| Rule | Value | Source |
|---|---|---|
| Text contrast | ≥ 4.5:1 (≥ 3:1 at ≥24px, or ≥18.66px bold) | WCAG 2.2 1.4.3 |
| UI component contrast | ≥ 3:1 vs adjacent colors | WCAG 2.2 1.4.11 |
| Pointer target | ≥ 24×24 CSS px; touch ≥ 44pt / 48dp | WCAG 2.5.8 · HIG · M3 |
| Body text | 15–25px, ≥16px in inputs | Butterick · mobile zoom |
| Line length | 45–90 chars (`max-width: 65ch`) | Butterick |
| Line height | ~1.5 body (1.4–1.6 works) · ~1.2 headings | M3 16/24 · Butterick 1.2–1.45 |
| Spacing | 4/8px scale | M3 |
| Animation | transform/opacity only, properties listed explicitly, reduced-motion honored | WCAG 2.3.3 · web.dev |
| Focus | visible indicator on every focusable element | WCAG 2.4.7 |
| Web Vitals | LCP ≤ 2.5s · INP ≤ 200ms · CLS ≤ 0.1 | web.dev |

**Quality floor.** Work in any mode ships responsive at 320px, keyboard-navigable with
visible focus, honoring `prefers-reduced-motion`. Interaction states that pure CSS can
provide (hover, focus, active, disabled) are styled; states that need runtime logic
(loading, empty, error) are built in Design mode and named as proposed follow-ups in Refit
mode, where behavior is frozen.

**The validator.** After producing or changing CSS/HTML, run:

```
python <skill-dir>/scripts/validate_ui.py <changed files or directory>
```

(`<skill-dir>` is the directory containing this SKILL.md.) Report its output honestly:
every FAIL is fixed or explicitly accepted by the user before the work is called done;
WARNs are listed with a one-line disposition each; ABSTAIN is reported as "not checkable",
never as a pass.

## Refit mode

Load `references/refit-playbook.md`, then:

1. **Scan silently:** framework, styling method, tokens, component conventions, two real
   pages. Tier the project (playbook: *Tier the project*) and open with that tier's move.
2. **State the preserve list** (playbook: *The preserve list*) to the user before the first
   edit, alongside what the audit found against the numbers table and `anti-defaults.md`.
3. **Plan at token level:** color (4–6 named hex values), type roles, spacing/radius/shadow/
   motion — plus one **Signature**: the single element this refresh will be remembered by.
4. **Critique the plan** before touching code: any part that reads as the generic default
   for "modernize this app" gets revised, and the revision is named to the user.
5. **Implement in slices** (playbook: *Incremental discipline*) — behavior verified per
   slice, committed per slice where the project uses git.
6. **Close with evidence:** what-changed/what-stayed summary keyed to the preserve list,
   validator output, and before/after screenshots when a browser is available.

The refit is done when the preserve list is intact, the validator reports no unaccepted
FAILs, and the user has seen the evidence — not when the CSS is written.

## Design mode

Load `references/anti-defaults.md`, then work in two passes:

1. **Plan:** ground the design in the subject (its audience, vocabulary, and the page's one
   job), then a compact token system — color as 4–6 named hex values, two-plus type roles,
   layout in a sentence, and one Signature element. When the brief reads as an existing
   design ecosystem, route to the real package (anti-defaults: *Route to the real system*).
2. **Critique, then build:** compare the plan against the generic default for this kind of
   page and against the anti-defaults list; revise what matches, say what changed; then
   build exactly the revised plan. Spend boldness on the Signature; keep the rest quiet.

Finish with the validator and the quality floor, same contract as Refit.

## Review mode

Load `references/review-rules.md` and follow its **Review output contract**: stated
assumptions, findings as P0/P1/P2 with `path:line`, a one-line diagnosis before every P0/P1
fix, a concrete fix per finding, and `PASS` (with scope) for a clean target. Review mode
reads and reports; the working tree is identical before and after. Run the validator on the
reviewed files and fold its findings in, labeled as machine-checked.
