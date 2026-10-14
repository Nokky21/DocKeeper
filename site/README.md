# dockeeper-site

The website at <https://nokky21.github.io/DocKeeper/>: one page built with Astro, laid out like a
document, with a demo that runs a small port of the check in the browser. It is the only package in
this repository; the root holds the skill and the CLI.

## Entry point

`src/pages/index.astro` assembles the sections from `src/components/`, inside
`src/layouts/Base.astro`, which holds the head, the header, the footer and the only script of the
page: tabs, copy buttons, the fade on commands that don't fit and the side index. The site is served
under `/DocKeeper/`, the path GitHub Pages gives this repository.
<!-- dockeeper: site/astro.config.mjs:6 -->

## What it offers

- **The page.** Ten numbered sections, from what DocKeeper writes to the questions, plus the hero.
  Every margin note carries the anchors of what it claims, so this site is checked like any other
  documentation of the repository.
- **The demo.** `src/demo/engine.ts` seals and checks in the browser. It is a port of the engine
  limited to what the demo needs: Python code, definitions found by `def` and `class`, and the
  verdicts `OK`, `MOVED` and `CHANGED`.
  <!-- dockeeper: site/src/demo/engine.ts#seal site/src/demo/engine.ts#verify site/src/demo/engine.ts#blockAt -->
- **Scenarios shared with the real engine.** `src/demo/scenarios.json` lists each change of the demo
  and the verdicts it must give. `tests/test_demo.py` runs them through the Python engine and
  `scripts/check-demo.ts` through the port, so both have to agree.
  <!-- dockeeper: tests/test_demo.py#PruebasDemo.test_la_demo_de_la_web_dice_lo_mismo_que_el_motor site/scripts/check-demo.ts#check -->

## Depends on / used by

- **Depends on:** Astro, and the Geist, Geist Mono and Newsreader fonts from Fontsource, bundled with
  the page instead of loaded from a third party. <!-- dockeeper: site/package.json:14 -->
- **Used by:** nothing imports it. The Website workflow builds it and publishes it to GitHub Pages.

## Develop and test

From `site/`, with Node 24 and `yarn`:

- `yarn install` once.
- `yarn dev` for a local server with live reload.
- `yarn test` to check that the demo agrees with the Python engine.
- `yarn build` for the static site in `dist/`.

<!-- dockeeper: site/package.json:9 .github/workflows/pages.yml:30 -->

## Known traps

- **The `.astro` files are documents for DocKeeper.** A literal `[[` or three backticks in them
  would be read as an anchor or a code fence: write `&#91;` and `&#96;` instead. Braces start an Astro
  expression, so literal ones are `&#123;` and `&#125;`.
- **The hero diagrams are Mermaid 11 renders inlined as SVG** (`src/assets/flujo-*.svg`). Their
  labels are `p` elements inside `foreignObject`, so page styles for `p` reach them, and an SVG
  inlined twice needs its ids changed.
- **The images in `public/assets/`** (diagrams, real terminal captures and the README banner) come
  from maintainer tools kept outside the repository; see [the procedures](../docs/procedures.md).

## Limits

The demo port knows only Python and the three verdicts above. Everything else, other languages,
published documents and the rest of the verdicts, is what the real CLI does.
