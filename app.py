from flask import Flask, render_template, request, url_for
from flask_caching import Cache
import requests

import samples

config = {
    "DEBUG": True,                  # some Flask specific configs
    "CACHE_TYPE": "SimpleCache",    # Flask-Caching related configs
    "CACHE_DEFAULT_TIMEOUT": 10,    # seconds
    "DEFAULT_LANGUAGE": "en",
    "LARGE_IMAGE_SIZE": 1000,
    "MIN_THUMB_SIZE": 200,
    "INTEGER_CANVASES": True        # Only for RAW manifests
}

WELLCOME = 'wellcome'
FRASER = 'fraser'
RAW = 'exploded'

app = Flask(__name__)
app.config.from_mapping(config)
cache = Cache(app)


@app.route('/iiif/<source>/<identifier>')
@cache.memoize()
def load_iiif(source, identifier):
    if source == WELLCOME:
        raw_url = f"https://iiif.wellcomecollection.org/presentation/{identifier}"
    elif source == FRASER:
        raw_url = f"xxx{identifier}"
    elif source == RAW:
        if identifier.startswith("http"):
            raw_url = identifier
        else:
            raw_url = f"https://{identifier}"
    else:
        raise ValueError("Unknown IIIF source")

    req = requests.get(raw_url)
    return req.json()


@app.route('/<source>/canvas/<path:path>')
def iiif_canvas(source, path):

    full_canvas_id = None
    canvas = None

    if source == WELLCOME:
        parts = path.split("/")
        manifest = load_iiif(WELLCOME, parts[0])
        full_canvas_id = get_canvas_id(WELLCOME, parts[0], parts[1])
    elif source == FRASER:
        # tbc, for now same logic
        parts = path.split("/")
        manifest = load_iiif(FRASER, parts[0])
        full_canvas_id = get_canvas_id(FRASER, parts[0], parts[1])
    elif source == RAW:
        manifest = load_iiif(RAW, path)
        canvas_q = request.args.get("canvas")
        # support index values and id values for canvas param
        if canvas_q.isdigit():
            canvas = manifest["items"][int(canvas_q)]
        else:
            full_canvas_id = canvas_q
    else:
        raise ValueError("Unknown IIIF source")

    if canvas is None:
        canvas = next((c for c in manifest["items"] if c["id"] == full_canvas_id), None)

    return render_template('canvas.html', model=get_page_model(source, manifest, canvas))


@app.route('/<source>/object/<path:path>')
def iiif_object(source, path):
    json = load_iiif(source, path)
    if json["type"] == "Collection":
        return render_template('collection.html', source=source, collection=json)
    else:
        return render_template('manifest.html', model=get_page_model(source, json))


def get_canvas_id(source, manifest_fragment, canvas_fragment):
    if source == WELLCOME:
        return f"https://iiif.wellcomecollection.org/presentation/{manifest_fragment}/canvases/{canvas_fragment}"
    elif source == FRASER:
        return None  # tbc
    elif source == RAW:
        return canvas_fragment

    raise ValueError("Unknown source")


# To be called by the template (instead of url_for)
def manifest_url(source, manifest):
    if source == WELLCOME:
        parts = manifest["id"].split("/")
        return f"/{WELLCOME}/object/{parts[-1]}"
    elif source == FRASER:
        # tbc, assume same for the moment
        parts = manifest["id"].split("/")
        return f"/{FRASER}/object/{parts[-1]}"
    elif source == RAW:
        return f"/{RAW}/object/{no_protocol(manifest['id'])}"

    raise ValueError("Unknown source")


# To be called by the template (instead of url_for)
def canvas_url(source, manifest, canvas):
    if source == WELLCOME:
        parts = canvas["id"].split("/")
        return f"/{WELLCOME}/canvas/{parts[-3]}/{parts[-1]}"
    elif source == FRASER:
        # tbc, assume same for the moment
        parts = canvas["id"].split("/")
        return f"/{FRASER}/canvas/{parts[-3]}/{parts[-1]}"
    elif source == RAW:
        if config["INTEGER_CANVASES"]:
            for idx, cvs in enumerate(manifest["items"]):
                if cvs["id"] == canvas["id"]:
                    return f"/{RAW}/canvas/{no_protocol(manifest['id'])}?canvas={idx}"
            raise ValueError(f"Can't find canvas {canvas['id']}")
        else:
            return f"/{RAW}/canvas/{no_protocol(manifest['id'])}?canvas={canvas['id']}"

    raise ValueError("Unknown source")


def get_text_lines(canvas):
    if canvas is None:
        return None
    annotation_pages = canvas.get("annotations", None)
    if annotation_pages is None or len(annotation_pages) == 0:
        return None
    # just use the first page for now and assume we need to load it
    # assume just one kind of anno
    try:
        req = requests.get(annotation_pages[0]["id"])
        annos = req.json()
        strings = []
        for anno in annos["items"]:
            body = anno.get("body", None)
            if body is not None and body.get("type", None) == "TextualBody":
                strings.append(body.get("value", ""))

        return strings
    except:
        return None

    return None


def get_page_model(source, manifest, canvas=None):
    page_model = {
        "source": source,
        "label": get_single_string(manifest, 'label'),
        "manifest": manifest,
        "total_canvases": len(manifest["items"]),
        "canvas": canvas,
        "prev_canvas": None,
        "next_canvas": None,
        "canvas_index": -1,
        "text_lines": get_text_lines(canvas),
        # helpers:
        "canvas_url": canvas_url,
        "manifest_url": manifest_url,
        "single_string": get_single_string,
        "strings": get_strings,
        "get_thumbnail": get_thumbnail,
        "get_static_image": get_static_image
    }
    if canvas is not None:
        for idx, cvs in enumerate(manifest["items"]):
            if cvs["id"] == canvas["id"]:
                page_model["canvas_index"] = idx
                if idx > 0:
                    page_model["prev_canvas"] = manifest["items"][idx - 1]
                if idx+1 < len(manifest["items"]):
                    page_model["next_canvas"] = manifest["items"][idx + 1]
                break

    return page_model


def no_protocol(old_url):
    new_url = old_url.removeprefix("https://")
    new_url = new_url.removeprefix("http://")
    return new_url


@app.route('/')
def index():
    model = []
    for manifest in samples.SAMPLES["items"]:
        id = manifest["id"]
        model_manifest = {
            "original": id,
            "label": get_single_string(manifest, "label"),
            "raw": url_for("iiif_object", source=RAW, path=no_protocol(id))
        }
        if id.startswith("https://iiif.wellcomecollection.org/presentation/"):
            model_manifest["internal"] = url_for("iiif_object", source=WELLCOME, path=id.split('/')[-1])
        elif id.startswith("(fraser)"):
            model_manifest["internal"] = model_manifest["raw"]
        else:
            model_manifest["internal"] = model_manifest["raw"]

        model.append(model_manifest)

    return render_template('index.html', label='The Exploded Viewer', model=model)


def get_single_string(iiif, prop_name, fallback=None, lang=config["DEFAULT_LANGUAGE"]):
    strings = get_strings(iiif, prop_name, fallback, lang)
    if len(strings) > 0:
        return strings[0]
    return ''


def get_strings(iiif, prop_name, fallback=None, lang=config["DEFAULT_LANGUAGE"]):
    lang_map = iiif.get(prop_name, None)
    if lang_map is not None:
        val = lang_map.get(lang, None)
        if val is None:
            val = lang_map.get("none", None)
            if val is None:
                val = next(lang_map.values, None)

        if val is not None:
            return val

    if fallback is None:
        return []

    return [fallback]


def get_static_image(canvas, preferred_size=config["LARGE_IMAGE_SIZE"]):
    painting_annos = canvas["items"][0]["items"]
    image_anno = next((anno for anno in painting_annos if anno["body"]["type"] == "Image" ), None)
    image_body = image_anno["body"]  # TODO handle multiple bodies, choice
    if image_body is None:
        return None

    return get_sized_image(image_body, preferred_size)


def get_thumbnail(canvas):
    thumbnails = canvas.get("thumbnail", [])
    if len(thumbnails) == 0:
        return get_static_image(canvas, config["MIN_THUMB_SIZE"])

    thumbnail = thumbnails[0]
    return get_sized_image(thumbnail, config["MIN_THUMB_SIZE"])


def get_sized_image(image, preferred_size):
    image_service = get_image_service(image)
    if image_service is None:
        return {
            "id": image["id"],
            "width": image.get("width", None),
            "height": image.get("height", None),
        }
    useful_size = None
    sizes = image_service.get("sizes", [])
    if len(sizes) > 0:
        for size in sizes:
            if size["width"] >= preferred_size or size["height"] >= preferred_size:
                if useful_size is None or useful_size["width"] > size["width"]:
                    useful_size = size
    if useful_size is not None:
        return {
            "id": f'{image_service["id"]}/full/{useful_size["width"]},{useful_size["height"]}/0/default.jpg',
            "width": useful_size["width"],
            "height": useful_size["height"]
        }
    else:
        # TODO we can optimise this further for smaller sizes.
        # Needs to work for level < 1: no !w,h unless profile supports it
        return {
            "id": f'{image_service["id"]}/full/!{preferred_size},{preferred_size}/0/default.jpg',
            "width": None,
            "height": None
        }


def get_image_service(image):
    if image is not None:
        services = image.get("service", [])
        image_service = next((s for s in services if s.get("type", "").startswith("ImageService")), None)
        return image_service
    return None


if __name__ == '__main__':
    app.run()
