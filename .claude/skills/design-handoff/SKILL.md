---
name: design-handoff
description: Implement a design_handoff_* dossier in this repo (Broadsheet design system: colors, spacing, HTML structure). Use when asked to implement a design handoff, when a design_handoff_* folder is referenced, or when editing templates/static files that such a folder documents.
---

1. **Find the dossier and the relevant section.** Locate the `design_handoff_*/` folder. Its `README.md` can bundle several numbered handoffs (`Handoff n°1`, `n°2`...) — read the one section covering the request in full; skimming it is not reading it.

2. **Read it as a spec, not inspiration.** Per `CLAUDE.md`, colors, spacing, and HTML structure in that section are final. Don't approximate a value, invent a class name, or "improve" the layout — match what's written.

3. **Map files to destinations.** The section's `Fichiers` list and `Prompt de départ pour Claude Code` name exactly which files go where (e.g. a stylesheet copied into `static/`, a template replacing one in `templates/`). The `.dc.html` files are prototypes to read for reference, never code to paste in as-is.

4. **Touch only what's named.** Routes, models, and business logic stay untouched unless the section explicitly says otherwise — most handoffs are template + stylesheet swaps. Keep existing form `name`/`id` attributes and endpoints exactly as they are.

5. **Verify.** Run `pytest`, then perform the section's own verification step named in its `Prompt de départ` (e.g. a print-to-PDF check, a hover state, a responsive breakpoint) — that step is the check, not optional polish.

**Done when:** every color, spacing value, and HTML element in the touched templates/CSS traces to a line in the handoff section — nothing invented, nothing skipped — `pytest` passes, and the section's own verification step has been carried out.
