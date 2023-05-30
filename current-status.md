# Current Status

### 2023-05-30

St Louis archive items are text-heavy - mostly printed text, rather than artworks. They are for reading, rather than looking at.

The previous implementation used PDFs, with each digitised page image overlaid with a text layer. PDFs are well suited to reading, obviously. And the user can download them and take them away.

But they have two major drawbacks:

1. They are enormous - many 100s of MB for a large document. This makes for a very poor user experience, and arbitrary breaking-up of works into smaller parts just to tackle page-weight.
2. They are not interoperable IIIF, with all the annotation, reuse, recombination and other benefits that IIIF brings.

The first iteration of this work focused on exploring ideas in [The Exploded Viewer](https://medium.com/digirati-ch/progressive-enhancement-digital-objects-and-the-exploded-viewer-b0594d7bbb52), with a web-page-per-item-page and support for non-script environments. Pages are simple HTML, with markup targeting assistive technologies.
Progressive enhancement added Canvas Panel to give us text overlay and deep zoom per-image (but not yet text overlay and deep zoom _at the same time_).

In the previous call with St Louis we discussed the fact that the majority of their content is images of printed text. Current IIIF viewers like Mirador and UV are obviously _readable_ (you can see the text) and even simulate some aspects of the layout (they understand page opening and present facing pages if correctly described in the published IIIF). But they are not optimised for _reading on the web_ - they lack the affordances of a PDF.

We spent some time looking at Wellcome Collection - where the majority of items are also printed text. Here, the work page viewer presents the pages as a vertical scroll, like a PDF, with deep zoom available as a separate interaction per-image.
This is more like the reading experience of a PDF. While full text search is available, and will highlight results on the image surface, you can't select text fromt he image surface.

What can we do to make the exploded viewer more PDF-like?

To begin, look at the un-enhanced version (no script) - make sure script is off on toggles:

https://st-louis-fed-exploded-viewer.azurewebsites.net/toggles

Then view a Manifest. 

There are now *two separate canvas views* so we can compare the previous version easily. The viewer defaults to the new version but you can access the old version as we will see in a moment.

With script off, the HTML contains all the thumbnails on the right but only the current canvas and its two neighbours on the right:

https://st-louis-fed-exploded-viewer.azurewebsites.net/wellcome/canvasv/b2101310x/b2101310x_0047.jp2

> There is a slight bit of trickery here as even with "script off" we do nudge the current canvas into the centre of the viewport, using script. The page would still work without that.

You can see the neighbouring two canvases - and you can scroll them, but no further. The images act as links to the new page for that canvas.

Now with script on, view the page again. The same HTML loads. 

Then script loads the IIIF Manifest, and builds out the left hand "PDF-like" view behind and ahead of the current canvas.

- Any full image that intersects the viewport is given a full image `src`.
- All the other images are set to use the thumbnail. On a reasonable connection and for a reasonably-sized manifest, this will usually have already loaded.
- This means that when you scroll the left hand window - with the mousewheel, gesture or by moving the scroll bar - you'll see actual pages whizzing past, helping you visualise the content.
- Once a scroll event finishes, the page ensures again that any full images intersecting the viewport are loaded.
- The first image whose top edge is inside the viewport is considered the current image.
- The thumbnail of the current image is highlighted (becomes active). 
- If the scroll has taken the thumbnail out of the viewport, we scroll the new thumbnail into view...
- ...but we don't make scroll position changes to the thumbnail panel if the new canvas thumbnail is still in view, so you can slowly scroll and move the active selection from top to bottom. This feels right.
- The browser address bar will update after a scroll event when the current image has changed - but this is a `replaceState` - it does not create an entry in the back-button history.
- The thumbnails no longer load a new page on click, instead they reposition the left viewport to the new Canvas. I think that unlike a scroll event, a thumbnail click _SHOULD_ update the browser history (using `pushState`) and that you can cycle back through previous thumbnail navigations with the browser back button. (I haven't implemented this yet).
- You can switch to the other (previous) view by changing `.../canvasv/...` to `.../canvas/...` in the address bar, which show you Canvas panel. There's also a link above the thumbnails on the new view that does this.


## Next - text selection within the extended view

 - Can we have something that appears to behave identically to this *and feels as fast* but that uses Canvas Panel - if not for all images then at least for the current image?
 - ...And that therefore allows *_text selection_*?
 - We would need Canvas Panel to load the single static image, not tiles, for performance.
 - This would allow text selection from the canvas (although not _running_ text selection).

## Next - transition to deep zoom

*What is the transition to deep zoom?* How does that work and how does it avoid feeling jarring? Can we retain the familiarity of the PDF-style reading experience with the ability to deep zoom when you want to, without two completely distinct states?

The first manifest shown above is a good example of something that doesn't need zoom - the whole thing is perfectly legible even at these fairly constrained sizes.

We're using a 1024 x 1024 confinement on the Wellcome images, but the St Louis "large thumbnail" could be bigger than this - 1500 would be a good choice.

However, with something like this:

https://st-louis-fed-exploded-viewer.azurewebsites.net/wellcome/canvasv/b21895466/b21895466_HB13_7_15_0154.JP2

...you're going to want to zoom in for a closer look - this is crying out for zoomable images. 

So what's the user interaction to get to them?

## Further TODO

 - Fix the prev / next buttons to the top of (the right viewport?) so they are always visible, and stop them from reloading the page
 - Support the Search API and support CTRL+F searching within the item
 - Keyboard navigation support to match PDF behaviour (using arrow keys to keep reading)
 - Allow the user to adjust the proportions of the two columns (make more room for thumbs or content as desired) 
 - What to do with the metadata (currently underneath the thumbs)?
 - What happens with a narrow viewport? Typically on a phone or tablet - rely on rapid panning/scrolling alone? Show a single-image vertical strip (that can be brushed aside)?

## Further production enhancements

 - Use responsive images rather than a fixed size. However, ensure that they correspond to advertised `sizes`
 - While the full images only load when the image is in the browser viewport, we are loading all the thumbnails. This has the benefit that the full image placeholders (which use the same thumbnail) are pre-cached so the user sees something as they scroll. But for very large manifests we are loading a lot of thumbnails. We can experiment with a balance between these two competing optimisations.
