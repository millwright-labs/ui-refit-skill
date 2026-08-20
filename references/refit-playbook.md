# Refit playbook

How to modernize an existing UI without breaking what works. A refit succeeds when the
product looks current, behaves identically, and the owner can list exactly what changed.

## Tier the project

Read the codebase before asking anything: framework, styling method (plain CSS / Tailwind /
CSS-in-JS / a design system), token or theme files, component conventions, and two or three
real pages. Then bucket the project and open with the matching move — one calibrated
question beats ten generic ones.

| Tier | Detection cue | Opening move |
|---|---|---|
| Blank | No UI code exists yet | This is Design-mode work — switch modes and say so in one line. |
| Half-built | Components exist, no coherent visual system | Propose a token system that absorbs the existing components; ask only about aesthetic direction. |
| Mature | Consistent tokens/design system already in place | Propose token-level changes only; list everything that stays; ask before touching component structure. |
| Messy legacy | Mixed eras, inline styles, dead CSS, no tokens | Propose extracting tokens first as its own slice, then refitting on top; warn that visual diffs will be noisy. |
| Uncertain | Can't tell what's load-bearing | Name what you can't determine and ask the one question that unblocks it. |

## The preserve list

State this list to the user before the first edit. These survive the refit byte-for-byte
unless the user explicitly asks otherwise:

- The tech stack and styling method — a refit restyles; it does not migrate frameworks.
- Runtime behavior — every flow that worked before works after, verified per slice.
- Route slugs and URL parameters — bookmarks and integrations depend on them.
- Form field `name`s and `id`s — backends and autofill depend on them.
- Analytics events, IDs, and `data-*` tracking attributes.
- Navigation labels and information architecture — users' spatial memory is a feature.
- Test selectors (`data-testid` and friends) — a refit that breaks the test suite shipped a bug.

If a preserve-list item is itself the problem (a nav label that misleads, a field name that
collides), changing it is a separate, named decision the user approves — never a side effect.

## The replace list

What a refit actively hunts, roughly in order of visual payoff:

- Dated visual tokens: era-marker gradients and bevels, tiny body text, system-default
  typefaces used by inertia, harsh pure-black-on-pure-white or low-contrast gray-on-gray.
- Missing interaction states. Absent presentation states (hover, focus-visible, active,
  disabled styling) are always in scope — pure CSS, no behavior change. States that need new
  runtime logic (loading, empty, error flows) get proposed as named follow-ups, never added
  silently.
- Off-scale spacing: values that ignore the project's grid (or the absence of any grid).
- Cliché patterns from `anti-defaults.md` — both the 2010s kind and the current
  AI-default kind.
- Weak hierarchy: pages where nothing is clearly first, headings that whisper, walls of
  same-size text.
- Decoration that outlived its job: stock icons next to every label, boxes inside boxes,
  dividers between things that spacing already separates.

## Incremental discipline

- Work in slices a reviewer could reject independently: tokens first, then one page or
  component family per slice.
- After every slice: exercise the affected flows (or run the project's tests), then commit.
  A refit is a series of small provable wins, not one big reveal.
- End with three artifacts: a what-changed / what-stayed summary keyed to the preserve
  list, the validator's output (`python <skill-dir>/scripts/validate_ui.py <changed files>`,
  where `<skill-dir>` is the directory containing SKILL.md), and before/after screenshots
  when a browser is available.

## Theming contract

When the refit introduces or reworks theming, the token architecture is:

- All colors defined as custom properties on `:root` — the complete light (or chosen
  default) palette lives there, and components consume only tokens.
- Dark palette via `@media (prefers-color-scheme: dark)`, redefining tokens only —
  never styling components directly inside the media block.
- If the app has a manual toggle, explicit `[data-theme="dark"]` / `[data-theme="light"]`
  token overrides win over the media query in both directions.
- Every color must resolve in the un-stamped state (no toggle attribute set): a color whose
  only definition sits inside a `[data-theme]` block never applies for first-time visitors.
- The body background is always painted from a token — a transparent body borrows whatever
  ground the host or browser paints, which is how one-theme-text-on-other-theme-ground
  bugs ship.
- The accent must hold on both grounds; if it fights one, shift it toward an analogous hue
  or drop its saturation for that theme rather than swapping it for a different color.
