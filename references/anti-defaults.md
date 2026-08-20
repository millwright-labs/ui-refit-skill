# Anti-defaults

**Reviewed: 2026-08-19 — re-verify quarterly.** This file describes what generated design
currently collapses into. It is calibration data, not law: these looks are defaults to avoid
*reaching for reflexively*, and an explicit user request for any of them wins without
argument. Expect this list to go stale as model defaults drift — check the review date.

## The current clichés

Each entry names the look and its tell-tale signs. Landing in one of these by accident is
the failure; landing in one on purpose, for a reason you can state, is a design choice.

- **Cream editorial.** Warm off-white ground (the #F4F1EA family), a high-contrast display
  serif, terracotta or burnt-orange accent. Reads as "tasteful" precisely because every
  generated portfolio now has it.
- **Void-plus-acid.** Near-black ground, one neon accent (acid green, vermilion), oversized
  grotesque type. The default costume for "developer tool".
- **Broadsheet cosplay.** Hairline rules everywhere, zero border-radius, dense
  newspaper-style columns and tiny caps labels — applied to content that isn't a newspaper.
- **Purple gradient hero.** A violet-to-indigo gradient (the #8B5CF6 / #6366F1 family)
  behind centered white text, usually with glassmorphic cards floating on it.
- **Reflex typefaces.** Inter or Space Grotesk chosen not because they fit the subject but
  because they're the statistically safe pick. Both are fine faces — as decisions, not defaults.
- **Emoji as information architecture.** An emoji prefixing every heading and list item,
  doing the job hierarchy and spacing should do.
- **Uniform rounded-everything.** The same large border-radius on every card, button, input,
  and image, regardless of nesting or scale.
- **Three equal feature cards.** The centered hero → three-icon-cards → testimonial → CTA
  scaffold, independent of what the product actually needs to say.
- **Glassmorphism everywhere.** Blur + transparency on every surface, killing contrast and
  hierarchy at once.

## Route to the real system

When the brief smells like an existing design ecosystem, the move is never to hand-fake its
CSS — install and use the real package, and say that's what you're doing:

| Brief smells like | Use |
|---|---|
| Google / Android / Material | Material Web / MUI (M3 tokens) |
| Microsoft / Windows / Office | Fluent UI |
| IBM / enterprise data tools | Carbon |
| UK government / public services | GOV.UK Design System |
| US government | USWDS |
| Modern React app, shadcn-style | shadcn/ui + Radix primitives |

## The positive move

Distinctiveness is not the negation of this list — it comes from the subject's own world:
its materials, instruments, vocabulary, and audience. Derive the palette and type from
something true about the subject, spend the boldness in **one Signature element**, and keep
everything around it quiet. If no part of the design would surprise a person who has seen a
hundred generated pages, revise the part that matters most first.
