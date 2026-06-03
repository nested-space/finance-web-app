# Design system

This document is the **mandatory** brand and visual-design contract for the
`finance_web_app` frontend. It sits over and above any framework defaults. Where
this file conflicts with a library's default styling, **this file wins**, and the
default is overridden. `web/static/css/app.css` is the implementation; this
document is the source of truth for intent.

A change that violates a MANDATORY rule below fails frontend review.

## 1. Colour balance and roles

Each colour has a distinct role, and the palette is deliberately unbalanced:

- **Slate Navy and White are predominant.** Slate Navy must be the *most prominent*
  colour in any design. White (and the neutral washes) carry the rest.
- **Secondary colours (teal, burnt sienna, muted violet, antique gold, steel blue)
  are used sparingly** — accents, and chart/data series only.

MANDATORY:

- **Secondary colours must never be used for backgrounds or for text.** They appear
  only in charts, data visualisations, small accents, and chart-linked value
  callouts (see §4).
- **Slate Navy must be the most prominent colour.** Every page is anchored by Slate
  Navy — at minimum the nav bar (see §8).

## 2. Palette (tokens)

These are the canonical tokens, mirrored verbatim in `app.css` `:root`.

```css
:root {
  /* Brand — Slate Navy */
  --brand:       #2D3F5C;
  --brand-hover: #223049;
  --brand-tint:  #E0E6F0;
  --brand-ink:   #FFFFFF;

  /* Secondary palette (accents + charts only — never bg or text) */
  --s1: #2A7A6F;  /* teal */
  --s2: #B5541A;  /* burnt sienna */
  --s3: #7B5EA7;  /* muted violet */
  --s4: #C49A1A;  /* antique gold */
  --s5: #4A7FA5;  /* steel blue */

  /* Secondary tints (charts/tables/infographics only — never type) */
  --s1-tint: #D0EAE7;
  --s2-tint: #F2DDD3;
  --s3-tint: #EAE4F4;
  --s4-tint: #F5EDCC;
  --s5-tint: #D8EAF4;

  /* Neutral */
  --ink:     #3F4444;   /* Graphite — body text */
  --muted:   #6B7280;   /* secondary text */
  --subtle:  #9DB0AC;   /* placeholders, icons */
  --line:    #CBD5D3;   /* borders, dividers */
  --surface: #EBEFEE;   /* Light Platinum — cards, sidebar */
  --wash:    #F2F2F2;   /* Platinum — page background */
  --canvas:  #FFFFFF;   /* modals, forms */

  /* Semantic */
  --danger:      #C0392B;  --danger-bg:  #FDE8E8;
  --success:     #16A34A;  --success-bg: #DCFCE7;
  --warning:     #D97706;  --warning-bg: #FEF3C7;
}
```

The **Slate Navy waterfall** uses `--brand` (most prominent) and steps down through
`--brand-tint`, `--surface`, `--wash` for successive sections. These brand neutrals
*are* allowed as backgrounds; the secondary `--sX` colours are not.

## 3. Accessible colour combinations

Accessibility is a legal requirement and the default, not an enhancement.

MANDATORY:

- Text and its background must meet **WCAG AA contrast** (≥ 4.5:1 normal, ≥ 3:1 large).
- Use only approved combinations: text in **Graphite (`--ink`), Black, White, or a
  core colour** on **White / neutral washes / Slate Navy** backgrounds. Slate Navy
  text on white, and white text on Slate Navy, are the workhorse pairs.
- Combinations outside the approved set (e.g. a secondary colour as a text or
  background colour) are **not permitted**.

## 4. Tints and shades

MANDATORY:

- Tints/shades of the palette are used **only in charts, tables, and infographics**,
  and in value callouts that visually link to a chart element (e.g. a widget whose
  background is `--sX-tint` to tie it to that series).
- **Never used for type.**
- Used in **steps of 20%**, never below 20% or above 80%.

## 5. White space

White space (areas with no design elements) is an essential brand element.

MANDATORY:

- **Do not fill the whole area with content.** Leave generous margins and gaps.
- White space creates the focal point — use it to make the message land. Panels
  breathe; content does not run edge to edge.

## 6. Typography — Inter

**Inter** is the only typeface. It is self-hosted under
`web/static/fonts/` (ExtraLight 200, Light 300, Regular 400, Bold 700); no CDN.
Stack: `'Inter', system-ui, -apple-system, 'Segoe UI', Roboto, sans-serif`.

Typesetting rules (web; scale type to the format):

| Role | Weight | Colour | Notes |
| --- | --- | --- | --- |
| **Heading (H1)** | Inter **ExtraLight/Light (200–300)**, larger | a core colour, Graphite, White, or Black | sentence case |
| **Sub-heading** | Inter **Light (300)** | core colour, Graphite, White, or Black | sentence case |
| **Intro / lead copy** | Inter **Bold (700)** | Graphite, White, Black (or Slate Navy to contrast the heading) | left aligned |
| **Body copy** | Inter **Regular (400)** | Graphite or Black | left aligned |
| **Feature numerals** | Inter **Bold** | a core colour | impact, ≤ heading size |
| **Feature copy** | Inter **Regular** | a core colour | impact, ≤ heading size |

MANDATORY:

- **Sentence case** for headings and sub-headings (not Title Case, not ALL CAPS).
- **Text is always left aligned.** No centred or justified body text.
- Tracking is tight: roughly **-0.01em** (the brand's "-10" character spacing).

## 7. Grid and panels

The grid divides a communication into **20 sections along its long edge** — a guide
to the eye for balanced proportions, **not a literal 20-cell grid**.

For a scrolling **website the long edge is vertical**, so the 20 sections are
**horizontal bands stacked down the page** (each band runs full-width, left to
right). They are *not* thin vertical columns — that orientation suits a landscape
slide, not a website. Panels stack vertically and each spans a run of consecutive
bands.

MANDATORY:

- A design uses **one to four panels** — **never more than four.**
- Panels span whole sections (bands) and stay aligned to the rhythm; they may be
  repositioned along it.

Reference proportions (header panel is band 1, measured down the page):

- *Four panels:* header `1`, panel `2–5`, panel `6–14`, panel `15–20`.
- *Three panels:* header `1`, panel `2–8`, panel `9–20`.

**Subdivision within a band is flexible** — e.g. two charts side by side in one
section. It is not governed by the 20-section guide, but it must look balanced and
professional (equal/considered widths, consistent gaps).

Implementation: the vertical band rhythm *is* the `.panel` stack (panels stacked in
`.container`). For in-section horizontal layout, `app.css` provides `.split` with
`.split-2` / `.split-3`, which stack on narrow viewports.

## 8. Panels, widgets, and Slate Navy presence

MANDATORY:

- **Sharp edges — no rounded corners** (`border-radius: 0`). 1px borders (`--line`)
  are the norm. The feel is professional and corporate.
- **A Slate Navy element anchors every page** — at minimum the nav bar is Slate Navy,
  and it is the most prominent colour. The landing/cover uses a full **Slate Navy
  header panel** for a strong first impression.
- **Do not put a full Slate Navy panel on every page** of a long flow — that becomes
  repetitive. After the nav, use the **tint waterfall** (`--brand-tint` → `--surface`
  → `--wash`) so Slate Navy adds rhythm rather than noise. Keep it balanced: present
  and prominent, never overwhelming.

## 9. Implementation pointers

- Tokens, `@font-face`, and component styles: `web/static/css/app.css`.
- Templates compose panels: `web/templates/` (`base.html` carries the Slate Navy nav).
- **No new frontend dependency** (CDN/npm/vendored library or font) without approval,
  per `ARCHITECTURE.md` → "Frontend asset boundary". Inter is the approved typeface.
- Charts (C3) are the only place the secondary palette and its tints appear; chart
  series map to `--s1`…`--s5`, callouts to `--sX-tint`.
