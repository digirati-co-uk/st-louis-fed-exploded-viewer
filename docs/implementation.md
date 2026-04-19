# IIIF Exploded Viewer — Implementation Notes

`docs/index.html` is a single self-contained static file: no build step, no framework, no server. It reads a IIIF Presentation API v3 manifest and renders it as a vertically-scrolling, PDF-like layout with selectable text overlays.

---

## Entry point

The page is opened with query parameters:

```
?manifest=<URL>&canvas=<canvasId>
```

`canvas` is optional. On load the script reads both parameters, pre-fills the manifest URL input with the manifest URL, then immediately `fetch()`es the manifest. If no `manifest` parameter is present the loading overlay is dismissed and the empty shell is shown.

---

## Layout

The layout is a CSS flexbox row that fills the full viewport height (`height: 100vh; overflow: hidden`):

```
┌──────────────────────────┬─┬─────────────────┐
│                          │ │ ← sticky header  │
│    scroll-panel (70%)    │d│   nav buttons    │
│                          │i│   manifest input │
│  canvas images stacked   │v│   title / count  │
│  vertically with gaps    │i│   text badge     │
│                          │d│─────────────────│
│                          │e│ thumbnail grid   │
│                          │r│ (scrolls         │
│                          │ │  independently)  │
└──────────────────────────┴─┴─────────────────┘
```

- **scroll-panel** — left column, `overflow-y: auto`, contains all canvas image containers stacked with `gap: 20px`.
- **divider** — 5 px drag handle, `cursor: col-resize`.
- **side-panel** — right column, flex column. The header (`side-panel-header`) is `flex-shrink: 0` so it stays pinned. The thumbnail grid is `flex: 1; overflow-y: auto` so it scrolls independently.

---

## Building the viewer (`buildViewer`)

After the manifest JSON is fetched, `buildViewer(manifest)` runs once:

1. Extracts the manifest label and page count and writes them to the header.
2. Inspects all canvases to determine the text overlay source and sets the badge (see below).
3. Fires `tryLoadManifestAnnotations(manifest)` — a single Promise that may fetch a manifest-level annotation bundle. This Promise is started **before** the canvas loop so all canvases share it rather than racing.
4. Iterates over `manifest.items` (the canvases), building a main-image container and a thumbnail item for each.
5. After the DOM is built, scrolls to the initial canvas and runs `upgradeVisibleImages`.

---

## Image sizing

Two IIIF Image API helpers drive image requests:

### `getSizedImage(imageBody, preferredSize)`

Picks the smallest listed size that is at least `preferredSize` pixels wide (or tall). If no size is large enough it picks the largest available. If the image service has no `sizes` array at all it returns `imageBody.id` unchanged. Used for thumbnails (called with `preferredSize = 0`, which always picks the smallest available size).

### `getLargestSizedImage(imageBody)`

Picks the largest entry in `service.sizes`. If `sizes` is absent it returns `imageBody.id` directly rather than constructing a URL from the service's native `width`/`height`, which would request the full-resolution image. This avoids oversized network requests when the manifest does not advertise discrete sizes.

### Two-phase image loading

For each canvas the image element is created with two sources:

- `img.src` is set immediately to the thumbnail URL (typically ~66 px). Because thumbnails are tiny, all of them load eagerly — there is never a blank placeholder while scrolling.
- `img.dataset.fullSrc` stores the largest listed size URL.

When the user stops scrolling (150 ms debounce), `upgradeVisibleImages` is called. It checks every canvas container against the scroll panel's bounding rect and sets `img.src = img.dataset.fullSrc` for any that are currently visible. This upgrades only images the user can actually see, without triggering an IntersectionObserver during scroll.

---

## Text overlay — three strategies

Each canvas gets an SVG element absolutely positioned over the image (`position: absolute; top: 0; left: 0; width: 100%; height: 100%`). The SVG uses a `viewBox` matching the canvas's pixel dimensions so all coordinate arithmetic is in canvas pixels; CSS scaling handles the rest.

Text elements are transparent (`fill: rgba(0,0,0,0)`) but carry a `::selection` rule that shows a blue highlight when the user selects text, making the overlay behave like a PDF text layer.

The viewer tries three strategies in order of preference:

### 1. Explicit SVG rendering (green badge — "SVG text overlays")

Example: [The transformations (or metamorphoses) of insects](https://digirati-co-uk.github.io/st-louis-fed-exploded-viewer/?manifest=https%3A%2F%2Fiiif.wellcomecollection.org%2Fpresentation%2Fb28047345)

Each canvas has a `rendering` entry:

```json
{
  "id": "https://iiif.wellcomecollection.org/svg/b28047345/b28047345_0059.jp2",
  "type": "Image",
  "format": "image/svg+xml"
}
```

The viewer fetches this URL (`cache: 'force-cache'`), parses the response as HTML, extracts the root `<svg>` element, strips its `width`/`height` attributes (so CSS controls sizing), adds the `text-overlay` class, and appends it to the container. No local SVG construction is needed.

### 2. Manifest-level annotation bundle (blue badge — "Text from manifest annotations")

Example: [The transformations (or metamorphoses) of insects — MUTATED](https://digirati-co-uk.github.io/st-louis-fed-exploded-viewer/?manifest=https%3A%2F%2Fdigirati-co-uk.github.io%2Fst-louis-fed-exploded-viewer%2Fb28047345.json)

The manifest has a top-level `annotations` array containing a page with the profile `https://dlcs.io/profiles/all-text`:

```json
{
  "id": "https://…/all-text-b28047345.json",
  "type": "AnnotationPage",
  "profile": "https://dlcs.io/profiles/all-text"
}
```

`tryLoadManifestAnnotations` detects this profile (exact URI match — other annotation pages on the manifest are ignored), fetches the single bundle file, and builds a `Map<canvasId, annotation[]>` by splitting each annotation's `target` on `#`:

```
"https://…/canvas/b28047345_0059.jp2#xywh=120,340,800,32"
 └── canvasId ──────────────────────┘  └── xywh fragment ┘
```

During the canvas loop, each canvas checks `manifestAnnos.has(canvas.id)`. If it matches, `buildSvgFromAnnotations` is called with the pre-loaded items — no further HTTP request is needed for that canvas.

The badge is set synchronously by checking whether `manifest.annotations` contains a page with the all-text profile, before the bundle is actually fetched.

### 3. Per-canvas annotation pages (yellow badge — "Text from per-canvas annotations")

Example: [The universe, or, The infinitely great and the infinitely little](https://digirati-co-uk.github.io/st-louis-fed-exploded-viewer/?manifest=https%3A%2F%2Fiiif.wellcomecollection.org%2Fpresentation%2Fb31356412)

Each canvas has its own annotation page:

```json
"annotations": [
  {
    "id": "https://iiif.wellcomecollection.org/annotations/v3/b31356412/b31356412_0132.jp2/line",
    "type": "AnnotationPage"
  }
]
```

If neither strategy 1 nor 2 applies, the viewer fetches `canvas.annotations[0].id`. Canvas width and height are taken from the annotation page's `partOf[0]` canvas reference if present, falling back to the canvas dimensions from the manifest. The result is passed to `buildSvgFromAnnotations`.

This means one HTTP request per canvas, fired as each canvas's `manifestAnnosPromise.then()` resolves (which resolves immediately with `null` when there is no manifest bundle).

### `buildSvgFromAnnotations`

Used by strategies 2 and 3. Replicates the algorithm in the server-side `SvgController.cs`:

- `viewBox` = `0 0 {canvas.width} {canvas.height}`
- For each annotation, parse `target` as `…#xywh=x,y,w,h`
- `<text x="{x}" y="{y + h*0.75}" textLength="{w}" font-size="{h}" lengthAdjust="spacingAndGlyphs" class="text-line-segment">`
- The y baseline at 75 % of the line height matches the server-side rendering

---

## Current-canvas tracking

A module-level `_currentIdx` variable records which canvas is considered "current". It is updated by `setCurrentCanvas`, which:

- enables/disables the Previous / Next buttons
- adds the `current` CSS class (blue border) to the active container
- adds the `active` class (blue border on thumbnail image) to the matching thumbnail item and smooth-scrolls it into view in the thumbnail panel
- updates `?canvas=<id>` in the URL via `history.replaceState` so the link remains bookmarkable without causing a page reload

`updateCurrentCanvas` scans the container list from the bottom and picks the last one whose top edge is within the upper half of the scroll panel — i.e., the last canvas the user has "passed". It is called on scroll stop (150 ms debounce).

The Previous / Next buttons call `navigateCanvas(±1)`, which calls `scrollIntoView({ block: 'center', behavior: 'smooth' })` then `setCurrentCanvas`.

---

## Resizable divider

The divider uses the Pointer Events API with `setPointerCapture` so pointer move events keep firing even if the cursor moves off the element quickly.

To avoid reflowing the entire canvas column on every mouse move (which is expensive with a large DOM), the resize is split into two phases:

1. **During drag** — only a lightweight fixed-position 2 px line (`#dragIndicator`) is moved. No layout changes occur.
2. **On release** (`pointerup`) — `scrollPanel.style.width` is updated once, causing a single reflow. The divider clamps the width so the scroll panel cannot shrink below 150 px or leave the side panel narrower than 125 px.

After the reflow, `_containerEls[_currentIdx].scrollIntoView({ block: 'center' })` restores the same canvas to the centre of the view. This is necessary because canvas heights change proportionally with the panel width (via `aspect-ratio`), so the previous scroll offset in pixels no longer corresponds to the same position in the document.

`user-select: none` is set on `document.body` while dragging and removed on release, preventing text from being accidentally selected during the drag.

---

## Error handling

If the manifest `fetch` throws a `TypeError` (network-level failure — CORS block, server not running, DNS failure) the error message distinguishes between localhost URLs and remote URLs:

- **localhost / 127.0.0.1** — hints that the server may not be running or may be missing `Access-Control-Allow-Origin: *`, and that opening the viewer as a `file://` URL prevents credentialled requests; suggests serving via `npx serve docs`.
- **Remote URL** — hints to check CORS headers.

HTTP errors (non-2xx responses) report the status code without a CORS hint, since the request reached the server.
