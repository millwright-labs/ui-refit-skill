# The research behind ui-refit

ui-refit was built after a structured review of the UI/UX skills people actually install for
Claude Code, plus a pass through the primary sources on what makes an interface good. This
document records what we read, what held up, and which findings became design decisions in
the skill. Research window: August 2026. Expect the competitive landscape to drift; the
primary-source numbers move much slower.

## Method

We read the files, not the READMEs: SKILL.md, reference documents, data files, and scripts
for eleven skills, official and community. Quotes were checked against the repos, and every
judging number below was verified against the standard or researcher that published it. Where
a page could not be fetched directly (Material Design's site renders client-side), the number
is marked with its corroboration instead of presented as first-hand.

## Four kinds of skill machine

Every UI/UX skill we read reduces to one of four mechanisms:

| Mechanism | What it does | Example |
|---|---|---|
| Direction prompt | Loads design opinions and a planning process before generation | anthropics/skills `frontend-design` |
| Rule linter | Checks finished UI code against a terse rule list | Vercel's `web-design-guidelines` |
| Data engine | Query scripts over bundled style/palette/typography data | `ui-ux-pro-max` |
| Reference library | Router file plus deep topic documents loaded on demand | `ux-designer-skill` |

Generation-time taste and review-time rigor almost never live in the same skill, and only one
skill we found anywhere (Anthropic's bundled dataviz skill, scoped to charts) closes the loop
with a script that can actually fail your output. ui-refit exists to put those pieces in one
place.

## What each skill taught us

**frontend-design (Anthropic).** 56 lines, and the strongest single idea in the field: draft
a compact token plan (colors, type roles, layout, one signature element), then critique that
plan against what you would produce for any similar brief, and only then write code. The
self-critique is the mechanism that prevents generic output; the style rules are raw
material for it. It also names the specific visual clichés generated design collapses into,
with hex values. What it lacks is any checkable number, any validator, and any concept of
working on an existing codebase. ui-refit adopts the two-pass loop and the signature concept
wholesale, and adds the parts it lacks.

**Web Interface Guidelines (Vercel, MIT).** Roughly a hundred MUST/SHOULD/NEVER rules,
most of them mechanically checkable ("Hit target ≥24px", "NEVER: transition: all"). The
modal tagging makes rules enforceable in a way prose never is. We also found a cautionary
tale in its packaging: the skill wrapper fetches its rules from a URL at every run, and the
repo holds two divergent copies, so agents following the wrapper never see the Design section
(shadows, radii, contrast model) that only exists in the other copy. ui-refit pins its rules
locally, and several rules in `references/review-rules.md` are adapted from this source under
its MIT license, tagged (WIG).

**dataviz and artifact-design (Anthropic, bundled with Claude Code).** dataviz is the most
rigorous skill we found: an ordered procedure with a runnable palette validator that
pass/fails color choices on lightness, chroma, and color-vision-deficiency separation. A
script that exits 1 changes agent behavior in a way advice does not. artifact-design
contributes a three-state theming contract (default, media-query dark, explicit toggle) that
prevents the classic unreadable-page bug where a color is only defined inside a theme block.
ui-refit's validator and its theming contract are structural copies of these two ideas,
re-scoped from charts and hosted artifacts to general web UI.

**ux-designer-skill (szilu).** Twenty-four reference files, about 11,700 lines, and the most
accurate sourcing we found anywhere. We spot-checked three of its claims against primary
sources (WCAG 2.2 target-size criterion, the European Accessibility Act enforcement date,
Apple's 44pt rule) and all three held. At review time it had 48 GitHub stars, which says
more about how this niche allocates attention than about the content. Its embedded
quick-numbers table (so trivial checks never load a reference file) became the numbers table
in ui-refit's SKILL.md.

**ui-ux-pro-max (nextlevelbuilder).** The engineering is genuine. A dependency-free BM25
search engine queries bundled CSVs (88 styles, 192 palettes, 74 font pairings), and an
explicit abstain-on-no-match rule returns "no match" instead of fabricated answers. The
content itself is competent-generic rather than curated, and the shipped data includes dead
columns (a "deprecated" placeholder string in every row we sampled of one file), which is
what volume without an editor looks like. We took the abstention pattern and the query-not-load architecture, and
declined the database approach itself.

**taste-skill (leonxlnx).** A sharp catalog of current model-default tells (named fonts,
named hex families, banned copy phrases) plus a routing table that sends briefs resembling
Material, Fluent, Carbon, or GOV.UK to the official package instead of hand-faked CSS. Its
weakness is treating those tells as permanent law when they are observations about this
generation of models, and advertising a unifying dial system its own sibling skills don't
use. ui-refit keeps the routing table idea and ships its cliché list with a review date and
an explicit instruction that a user's request overrides it.

**ui-ux-guide (oil-oil).** The only skill we found with a behavioral eval suite: JSON cases
asserting things like "a supplied brand color gets locked, not re-litigated" and "a kids' app
must not get defaulted into corporate minimalism." It also has the best review discipline,
tagging findings P0/P1/P2 and forcing a diagnosis (can the user not find the action, or not
tell what happened?) before any fix. Both patterns are in ui-refit: the eval suite shape in
`evals/`, the diagnosis-before-fix contract in Review mode. One flag: a feature its
description advertised was absent from the repo when we read it, which is why our evals test
the skill's actual behavior rather than its marketing.

**superdesign (superdesigndev).** A workflow wrapper around a hosted design tool, so not a
template for a self-contained skill, but two of its rules travel well: describe structure
rather than adjectives when reproducing an existing page, and never let a reworded request
silently trigger an expensive cold re-analysis.

**brand-guidelines and canvas-design (Anthropic).** The remaining two: a fixed brand-token
table applied mechanically, and a static poster-art skill. Narrow on purpose, and the first
one settled a design decision by example — brand tokens live in their own small skill, kept
apart from aesthetic judgment, which is why ui-refit ships without any brand data baked in.

## The judging framework

Four buckets, from measured-with-users down to checkable-by-script. ui-refit encodes buckets
C and D directly; A and B inform its review rules.

**A. Outcome metrics** (measure with real users): task success rate, time on task, error
rate (Nielsen Norman Group); effectiveness/efficiency/satisfaction (ISO 9241-11:2018); the
HEART framework (Rodden, Hutchinson & Fu, CHI 2010); the System Usability Scale, where 68 is
the average across 500+ studies (Sauro, MeasuringU).

**B. Heuristics** (expert evaluation): Nielsen's ten usability heuristics, and the
research-backed Laws of UX (Fitts, Hick, Jakob, Miller, the aesthetic-usability effect, the
~400ms Doherty threshold).

**C. Craft numbers** (checkable): text contrast ≥4.5:1, or 3:1 for large text (WCAG 2.2
1.4.3); component contrast ≥3:1 (1.4.11); pointer targets ≥24×24 CSS px (2.5.8) and 44pt/48dp
on touch (Apple HIG; Material 3); body text 15–25px with line-height 120–145% and a 45–90
character measure (Butterick, Practical Typography); spacing on a 4/8px grid (Material 3);
visible focus (2.4.7); animation on transform/opacity with reduced-motion honored (2.3.3).

**D. Performance and accessibility as UX:** LCP ≤2.5s, INP ≤200ms, CLS ≤0.1 at the 75th
percentile (web.dev); reflow at 320px (1.4.10); text-spacing survival (1.4.12); status never
carried by color alone (1.4.1). The European Accessibility Act has applied since 28 June
2025 to the consumer services it scopes (e-commerce among them, with microenterprise and
grace-period exemptions) — for in-scope services, the AA rows above are a legal requirement,
not a preference.

## Findings that became design decisions

1. **Plan, critique, build.** The self-critique pass is the anti-generic mechanism.
   Style rules feed it. (SKILL.md, Refit step 4 and Design pass 2.)
2. **A script that can fail you beats advice.** Hence `scripts/validate_ui.py`, with FAIL
   reserved for unambiguous defects and WARN for judgment calls, and an explicit ABSTAIN
   state instead of silent passes.
3. **Refits preserve by default.** Route slugs, form field names, analytics attributes, and
   test selectors survive byte-for-byte, and the preserve list is stated before the first
   edit. No skill we reviewed made this contract explicit; it is ui-refit's core.
4. **Cliché lists expire.** Ours carries a review date and loses to an explicit user request.
   In our own baseline test, an unassisted model asked for a finance landing page reached for
   Inter and a stock navy split-hero, which is why the list exists at all.
5. **Pin your rules.** The Vercel fork/drift finding; no runtime fetches.
6. **Popularity is a weak signal here.** The best-sourced reference set we found had 48
   stars; repos with six-figure star counts shipped placeholder data. We read files before
   trusting anything, and suggest you do the same, including with this repo.
7. **Test behavior, not vibes.** The eval suite asserts decisions (gate holds, preserve list
   survives, brand tokens lock) across models, with results published in `evals/RESULTS.md`.

## Sources

- Nielsen Norman Group — nngroup.com/articles/ten-usability-heuristics · usability-metrics
- W3C WCAG 2.2 — w3.org/TR/WCAG22
- APCA — apcacontrast.com
- ISO 9241-11:2018 — iso.org (Online Browsing Platform)
- Rodden, Hutchinson & Fu, "Measuring the User Experience on a Large Scale" (CHI 2010)
- Sauro — measuringu.com/sus
- web.dev/articles/vitals
- Apple Human Interface Guidelines — developer.apple.com/design/tips
- Material Design 3 — m3.material.io (client-rendered; figures corroborated via cached copies)
- Butterick, Practical Typography — practicaltypography.com/summary-of-key-rules.html
- Laws of UX — lawsofux.com
- Vercel Web Interface Guidelines (MIT) — github.com/vercel-labs/web-interface-guidelines
- anthropics/skills — github.com/anthropics/skills
- szilu/ux-designer-skill · nextlevelbuilder/ui-ux-pro-max-skill · leonxlnx/taste-skill ·
  oil-oil/ui-ux-guide · superdesigndev/superdesign-skill
