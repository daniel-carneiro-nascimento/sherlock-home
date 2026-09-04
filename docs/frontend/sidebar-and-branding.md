# Sidebar and Banner Visual Update

This update keeps the Sherlock Home frontend JavaScript-free.

## What changed

- collapsible desktop sidebar;
- off-canvas mobile sidebar;
- pure-CSS viewport size indicator;
- approved detective-boy mascot from the Sherlock Home banner;
- banner-inspired navy / cyan / blue / green / tan palette;
- subtle radial glow and circular detective-lens motifs;
- retained light and dark theme support;
- retained chart accessibility palettes;
- no browser JavaScript added.

## Sidebar behavior

Desktop:

```text
expanded  -> 268 px
collapsed -> 82 px
```

Mobile:

```text
closed -> off canvas
open   -> up to 82vw / 290 px
```

The same HTML checkbox controls both modes with CSS media queries.

## Viewport indicator

The top bar identifies the active layout range without JavaScript:

```text
XL       >= 1440 px
Desktop  1100-1439 px
Tablet   760-1099 px
Mobile   < 760 px
```

It is a CSS breakpoint indicator, not an exact `window.innerWidth` measurement.

That is deliberate: exact live pixel width would require JavaScript, while the useful information for this application is which responsive layout is active.

## Brand direction

The palette is derived from the approved Sherlock Home banner:

- deep navy / near-black background;
- cyan / teal;
- electric blue;
- green;
- warm detective-cap tan;
- limited purple and orange accents.

The interface avoids excessive red and keeps alert severity semantically separate from ordinary spending visuals.
