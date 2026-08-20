# Eval results

Run date: 2026-08-19. Cases: `cases.json`. Each case ran in a fresh agent session with the
skill installed at `~/.claude/skills/ui-refit`; prompts contained no mention of the skill, so
these runs also test natural triggering from the skill description. Behavior assertions were
judged from the agents' outputs; artifact assertions were verified independently with diffs,
greps, and validator runs against the produced files — not from the agents' self-reports.

## Baselines (no skill installed)

- **Design baseline (Claude Sonnet):** asked for a finance-app landing page, the unassisted
  model chose Inter and a stock navy split-hero, and its output failed the validator
  (3 contrast FAILs, 18 distinct font sizes, off-grid spacing). This is the default the
  skill exists to move away from.
- **Gate baseline (Claude Sonnet):** asked a functional question about ugly UI code, the
  unassisted model answered correctly and did not redesign. The gate risk is therefore the
  skill *over*-triggering once installed — which is what case 1 tests.

## Results — Claude (session model, 2026-08-19)

| Case | Result | Verified by |
|---|---|---|
| gate-holds | PASS | Correct bug answer; zero unrequested redesign; dir byte-identical (diff) |
| refit-preserves | PASS | All 11 preserve strings + 3 test ids byte-intact (grep); era markers 0 (grep); validator 0/0 on live files |
| plan-then-critique | PASS | Agent quoted its token plan and its critique verbatim, both produced before the first file edit ("My first-reflex plan was Inter + Tailwind blue-600… exactly the generic default, so it got revised") |
| no-cliche-landing | PASS* | Validator 0 FAIL / 0 WARN after the warm-bias refinement (below); no violet family (grep); subject-derived ledger design |
| brand-lock | PASS | #7D2E45 and Source Serif 4 present and load-bearing (grep); no Inter/Space Grotesk/violet hexes (grep) |
| existing-system-respect | PASS | Zero hex literals outside tokens.css (grep); changes made at token level |
| review-read-only | PASS | All 5 planted defects found with P0/P1/P2 + file:line + diagnosis; dir byte-identical (diff) |
| review-no-invention | PASS | PASS verdict with checked-scope list; one honest measured P2; dir byte-identical (diff) |
| validator-invoked | PASS | Validator run and reported (3 FAIL → 0 FAIL); preserved script behavior exercised live |
| ambiguity-one-line | PASS | Mode announced in one line, then full refit process; preserve sweep clean (grep) |

\* Scored against the refined check. Details under "What the run changed".

## Portability (gate case)

- **GPT-5.2 (Codex CLI, read-only):** read the skill unprompted, answered the bug with
  file:line references, produced zero unrequested redesign. Gate holds.
- **Gemini (agy lane):** answered the bug, then executed Step 0's offer shape exactly — two
  sentences naming the worst issue (2.85:1 body text) and offering a refit. Gate holds.
- Haiku was not tested in this run. Until it is, treat small models as unverified rather
  than supported.

## What the run changed (test-and-fix, recorded honestly)

1. **Validator: custom-property scanning.** The cliché-color check originally skipped
   `--var:` definitions, so token-based stylesheets (i.e., exactly what the skill tells
   agents to write) evaded it. Fixed; fire and control tests added.
2. **Validator: warm-bias gate on the cream family.** Pure RGB-distance flagged cool
   off-whites (`#F7F7F5`, `#F2F4F8`) as "AI-default cream". The cliché is the warm tone, so
   cream matches now also require r ≥ g ≥ b with r−b ≥ 6. Four control tests added.
3. **cases.json: the no-cliche assertion** originally banned any color within RGB distance
   16 of the cream hexes, which contradicted the skill's own definition of the cliché (the
   warm trio, not any near-cream paper) and would have failed a green-tinted ledger design
   that a designer would accept. The assertion now defers to the validator as the single
   source of truth. This is a test-spec correction, not a threshold loosened to pass a
   failing run — the violet family and the trio ban are unchanged.

## Known limits of this run

- "Plan/critique before first edit" ordering was proven verbatim for one refit case; the
  other refit cases were verified on artifacts and final reports, not full transcripts.
- Fresh-agent runs shared this machine's global agent configuration; three agents invoked
  their own external review lanes mid-run (and caught real issues: a focus-ring contrast
  miss, a 16px input floor break). That behavior comes from the machine's config, not from
  ui-refit — expect it not to reproduce elsewhere.
- One run per case per model. Single runs demonstrate the mechanism; they do not measure
  variance.
