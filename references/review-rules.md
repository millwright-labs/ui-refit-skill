# Review rules

The ruleset for Review mode, and the checklist Refit/Design runs before calling work done.
Source tags: (WCAG x.x.x) = WCAG 2.2 success criterion · (HIG) = Apple Human Interface
Guidelines · (M3) = Material Design 3 · (web.dev) = Core Web Vitals · (Butterick) =
Practical Typography · (WIG) = adapted from Vercel's Web Interface Guidelines (MIT).

## Focus & keyboard

- MUST: Every interactive element is reachable with Tab, in an order that follows the page.
- MUST: Every focusable element shows a visible focus indicator; removing `outline` requires
  an equal-or-better `:focus-visible` replacement. (WCAG 2.4.7)
- MUST: The focused element is never fully hidden behind sticky headers or overlays. (WCAG 2.4.11)
- MUST: Every drag, swipe, or gesture interaction has a click and keyboard alternative. (WCAG 2.5.7)
- MUST: Modals and menus close on Escape and return focus to the element that opened them.
- MUST: Real elements for real jobs — `<button>` for actions, `<a href>` for navigation. (WIG)
- NEVER: `tabindex` greater than 0.

## Targets & forms

- MUST: Pointer targets ≥ 24×24 CSS px; on touch, ≥ 44pt / 48dp — expand the hit area when
  the visual is smaller. (WCAG 2.5.8, HIG, M3)
- MUST: Every input has a visible label; a placeholder is not a label.
- MUST: Inputs declare the right `type`, `autocomplete`, and `inputmode` (email, tel, numeric).
- MUST: Inputs use ≥ 16px font-size (prevents mobile browser zoom-on-focus).
- MUST: Errors appear next to the field, name the field, and say what's wrong and how to fix it.
- MUST: Submit buttons say what they do — "Save API key", never bare "Submit"/"Continue". (WIG)
- SHOULD: Validate on blur or submit; while the user is still typing, stay quiet.
- SHOULD: Long forms warn before discarding unsaved input.
- NEVER: Block paste in inputs. (WIG)

## States & feedback

- MUST: Every interactive surface defines loading, empty, error, and success states — a
  missing state is a defect, not missing polish.
- MUST: Every action closes the loop: the user can tell it worked, what changed, and what's next.
- MUST: Destructive actions are reversible (undo window) or deliberately confirmed. (WIG)
- MUST: Status is conveyed by more than color alone; status icons carry text. (WCAG 1.4.1)
- MUST: Filters, tabs, pagination, and expanded panels are reflected in the URL and deep-link. (WIG)
- SHOULD: Loading skeletons mirror the final layout so content doesn't jump. (WIG)
- SHOULD: Mutations confirm within ~500ms — optimistic UI or a fast server round-trip. (WIG)

## Animation

- MUST: `prefers-reduced-motion` gets a reduced or removed variant of every animation. (WCAG 2.3.3)
- MUST: Nothing flashes more than three times per second. (WCAG 2.3.1)
- NEVER: `transition: all` — list the animated properties explicitly. (WIG)
- NEVER: Animate layout properties (`top`/`left`/`width`/`height`); animate `transform` and
  `opacity`. (WIG, web.dev)
- SHOULD: Micro-interactions run 150–300ms; one orchestrated moment beats scattered effects.

## Layout & responsiveness

- MUST: Usable at 320px width with no horizontal page scroll. (WCAG 1.4.10)
- MUST: Wide content — tables, code, diagrams — scrolls inside its own container, never the page.
- MUST: Content survives user text-spacing overrides (line-height 1.5×, spacing bumps). (WCAG 1.4.12)
- SHOULD: Spacing sits on a 4/8px scale; off-scale values are deliberate and rare. (M3)
- SHOULD: Mobile layouts respect safe-area insets. (WIG)
- SHOULD: Nested radii stay concentric — child radius ≤ parent radius. (WIG)
- SHOULD: Shadows are layered (ambient + direct) and tinted toward the background hue,
  not flat black. (WIG)

## Color & contrast

- MUST: Text contrast ≥ 4.5:1; ≥ 3:1 for large text (≥ 24px, or ≥ 18.66px bold). (WCAG 1.4.3)
- MUST: UI components and meaningful graphics ≥ 3:1 against adjacent colors. (WCAG 1.4.11)
- MUST: Colors live in tokens (custom properties); component styles consume tokens, not literals.
- MUST: Dark mode is its own resolved palette at the token level — never a naive inversion —
  and every color resolves in the default, un-toggled state.
- MUST: The body background is painted explicitly from a token.
- SHOULD: Check APCA for higher-fidelity contrast (≈ Lc 60 body floor, Lc 90 preferred).
- SHOULD: Semantic colors (success / warning / error) are distinct from the brand accent.

## Typography

- MUST: Body text 15–25px with line-height 1.4–1.6; headings ~1.1–1.3. (Butterick)
- MUST: Reading measure 45–90 characters — `max-width: 65ch` is the workhorse. (Butterick)
- SHOULD: One type scale with a fixed ratio; at most two typeface families plus a utility mono.
- SHOULD: `text-wrap: balance` on headings; `font-variant-numeric: tabular-nums` where digits align.
- NEVER: Justified text on the web without hyphenation. (Butterick)

## Copy

- MUST: Names describe what the user controls, not how it's built ("notifications", not
  "webhook config").
- MUST: Buttons are verb + object; errors say what happened and how to fix it — an apology
  is not an error message.
- SHOULD: Sentence case throughout, except deliberately styled brand labels.
- NEVER: Filler adjectives ("seamless", "elevate") where information could be.

## Performance

- MUST: LCP ≤ 2.5s, INP ≤ 200ms, CLS ≤ 0.1 at the 75th percentile. (web.dev)
- MUST: Images declare `width`/`height` or `aspect-ratio` so nothing shifts on load.
- SHOULD: Virtualize lists beyond ~50–100 rows. (WIG)
- SHOULD: Lazy-load below-the-fold images; preload the LCP image.
- NEVER: Layout reads (offsetHeight etc.) inside scroll handlers — batch reads in
  requestAnimationFrame.

## Review output contract

Review mode reads; it never edits. The report is:

1. One line of stated assumptions (platform, primary user, primary task) — guessed if
   unstated, and labeled as guesses.
2. Findings grouped by file as `path:line`, each tagged:
   - **P0** — breaks task completion or violates a MUST above.
   - **P1** — real friction; a SHOULD violation with user-visible cost.
   - **P2** — polish.
3. Every P0/P1 opens with a one-line diagnosis before its fix: an **execution** problem
   (the user can't find or perform the action) or an **evaluation** problem (the user can't
   tell what happened) — and for errors, a **slip** (right intent, wrong motion → fix with
   safer targets/undo) vs a **mistake** (wrong mental model → fix with naming/mapping).
4. Every finding ends with a concrete fix, not advice.
5. A clean target gets `PASS`, a list of what was checked, and zero invented findings.
   Report the issues that matter; padding a review is itself a review failure.
