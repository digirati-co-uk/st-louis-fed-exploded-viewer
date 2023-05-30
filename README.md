# st-louis-fed-exploded-viewer

Demo site to experiment with server-side IIIF rendering and progressive enhancement.

https://st-louis-fed-exploded-viewer.azurewebsites.net/

[Current status](current-status.md)


### Pass 1

 - No Javascript at all
 - Textual annotations displayed
 - `aria-describedby` to connect text and image
 - `aria-current` for active thumbnail
 - friendly URLs
 - Content dumped to HTML with some light bootstrap
 
In the first pass, it's tailored to Wellcome and Fraser manifests and probably won't work with random other manifests. It makes assumptions about what to find in the manifests which won't apply universally.

It understands the structure of Wellcome IIIF URLs and makes its own page URLs use their path elements.
Use the "raw url" option to see what the manifest and canvas view URLs would look like for a non-optimised source.

#### Optimised

 - Manifest: https://st-louis-fed-exploded-viewer.azurewebsites.net/wellcome/object/b2101310x
 - Canvas: https://st-louis-fed-exploded-viewer.azurewebsites.net/wellcome/canvas/b2101310x/b2101310x_0068.jp2

#### Unoptimised (raw url)

 - Manifest: https://st-louis-fed-exploded-viewer.azurewebsites.net/exploded/object/iiif.wellcomecollection.org/presentation/b2101310x
 - Canvas: https://st-louis-fed-exploded-viewer.azurewebsites.net/exploded/canvas/iiif.wellcomecollection.org/presentation/b2101310x?canvas=67

An even longer url would use the canvas id rather than index.
 
Later, we can user Vault on the server to handle _any_ manifest, not just Wellcome and Fraser ones.

### Pass 2 - design for visual and assistive technologies

The visual design is pretty poor. So before any more progressive enhancement we need to improve it, both for visual browsers and for assistive technologies.

 - How should the parts of the canvas page - image, page text, thumbs and metadata - be arranged visually?
 - What order should the HTML elements appear in?
 - Are the `aria-` attributes correct? What else do we need to have in the markup?
 - What should the pages offer to search engines? meta tags, etc.
 
### Pass 3, JavaScript enhancement
  
 - Use [Canvas Panel](https://iiif-canvas-panel.netlify.app/)
 - Use https://st-louis-fed-exploded-viewer.azurewebsites.net/toggles to change behaviour
 - Use Canvas Panel text features (overlay, copy and paste)
 
### Pass 4, partial SPA-fication:

 - With JS enabled, app doesn't make whole-page transitions. It updates the browser history but becomes more viewer-like in interaction, making partial page requests and/or using the IIIF Manifest directly.
 
