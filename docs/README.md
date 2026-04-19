## Samples

_See [implementation.md](implementation.md) for full details._

### Manifest with per-canvas SVG

[https://digirati-co-uk.github.io/st-louis-fed-exploded-viewer/?manifest=https%3A%2F%2Fiiif.wellcomecollection.org%2Fpresentation%2Fb28047345](The transformations (or metamorphoses) of insects)

Each Canvas has a `rendering` property linking to SVG XML:

```jsonc
{
    "...": "...",
    "type": "Canvas", // Canvas
    "...": "...",
    "rendering": [
        {
            "id": "https://iiif.wellcomecollection.org/svg/b28047345/b28047345_0059.jp2",
            "type": "Image",
            "label": { "en": [ "SVG XML for page text" ] },
            "format": "image/svg+xml"
        }
    ]
}
```

The viewer uses the SVG directly as the overlay source.


### Manifest with W3C annotations

[https://digirati-co-uk.github.io/st-louis-fed-exploded-viewer/?manifest=https%3A%2F%2Fiiif.wellcomecollection.org%2Fpresentation%2Fb31356412](The universe, or, The infinitely great and the infinitely little)

Each canvas has a link to `annotations`:

```jsonc
{
    "...": "...",
    "type": "Canvas", // Canvas
    "...": "...",
    "annotations": [
        {
            "id": "https://iiif.wellcomecollection.org/annotations/v3/b31356412/b31356412_0132.jp2/line",
            "type": "AnnotationPage",
            "label": { "en": [ "Text of page 104" ] }
        }
    ]
}

```

The viewer computes the SVG (using the same approach taken server-side on the previous manifest) and generates the overlay.

> Note that if this particular Manifest is re-processed at Wellcome, it will acquire SVG annotations on the server and will use them by default.

### Manifest with single all-text annotation page

[https://digirati-co-uk.github.io/st-louis-fed-exploded-viewer/?manifest=https%3A%2F%2Fdigirati-co-uk.github.io%2Fst-louis-fed-exploded-viewer%2Fb28047345.json](The transformations (or metamorphoses) of insects - MUTATED)

This Manifest has been _augmented_ by DLCS text services; it has a `manifest.annotations` property that links to a single file containing ALL the annotations:

```jsonc
{
    "...": "...",
    "type": "Manifest", // Manifest
    "...": "...",
    "annotations": [
        {
            "id": "ttps://digirati-co-uk.github.io/st-louis-fed-exploded-viewer/all-text-b28047345.json",
            "type": "AnnotationPage",
            "profile": "https://dlcs.io/profiles/all-text",
            "label": { "en": ["Text of all canvases"] }
        }
    ]
}
```

This annotation has the `profile` property "https://dlcs.io/profiles/all-text". The client needs this to avoid interpreting other manifest-level annotations as the full text.

