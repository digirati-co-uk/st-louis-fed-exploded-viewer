import json

from flask import Flask, render_template, request, url_for, make_response, g
from flask_caching import Cache
from functools import wraps
import requests

import samples

config = {
    "DEBUG": True,                  # some Flask specific configs
    "CACHE_TYPE": "SimpleCache",    # Flask-Caching related configs
    "CACHE_DEFAULT_TIMEOUT": 10,    # seconds
    "DEFAULT_LANGUAGE": "en",
    "LARGE_IMAGE_SIZE": 1000,
    "MIN_THUMB_SIZE": 0,
    "INTEGER_CANVASES": True        # Only for RAW manifests
}

WELLCOME = 'wellcome'
FRASER = 'fraser'
RAW = 'exploded'
WELLCOME_HOST = 'iiif.wellcomecollection.org'
FRASER_HOST = 'iiif-dev.slf.digirati.io'

app = Flask(__name__)
app.config.from_mapping(config)
cache = Cache(app)


def set_toggle_model(f):
    @wraps(f)
    def decorated_func(*args, **kwargs):

        # For any request, a toggle set on the query string takes precedence over cookies
        if "script_on" in request.args:
            script_on = bool(request.args["script_on"])
        else:
            script_on = bool(request.cookies.get('script_on'))

        if "show_text" in request.args:
            show_text = bool(request.args['show_text'])
        else:
            show_text = bool(request.cookies.get('show_text'))

        if "default_cp_text" in request.args:
            default_cp_text = bool(request.args["default_cp_text"])
        else:
            default_cp_text = bool(request.cookies.get('default_cp_text'))

        # But may be overridden by a form submission:
        if request.method == 'POST':
            if request.form.get('script_on', None):
                script_on = bool(request.form.get('script_on'))
            if request.form.get('show_text', None):
                show_text = bool(request.form.get('show_text'))
            if request.form.get('default_cp_text', None):
                default_cp_text = bool(request.form.get('default_cp_text'))

        g.model = {
            "script_on": script_on,
            "show_text": show_text,
            "default_cp_text": default_cp_text
        }

        response = make_response(f(*args, **kwargs))

        if script_on:
            response.set_cookie("script_on", str(script_on))
        else:
            response.set_cookie("script_on", "False", expires=0)
        if show_text:
            response.set_cookie("show_text", str(show_text))
        else:
            response.set_cookie("show_text", "False", expires=0)
        if default_cp_text:
            response.set_cookie("default_cp_text", str(default_cp_text))
        else:
            response.set_cookie("default_cp_text", "False", expires=0)

        return response

    return decorated_func


@app.route('/cptest')
def cp_test():
    return render_template('cp-test.html')


@app.route('/iiif/<source>/<identifier>')
@cache.memoize()
def load_iiif(source, identifier):
    if source == WELLCOME:
        raw_url = f"https://iiif.wellcomecollection.org/presentation/{identifier}"
    elif source == FRASER:
        raw_url = f"https://{FRASER_HOST}/presentation/{identifier}"
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
@set_toggle_model
def iiif_canvas(source, path):
    return render_canvas_template(path, source, "canvas")


@app.route('/<source>/canvasv/<path:path>')
@set_toggle_model
def iiif_canvas_v(source, path):
    return render_canvas_template(path, source, "canvasv")


def render_canvas_template(path, source, template):
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
    rendered = render_template(f"{template}.html",
                               model=get_page_model(source, manifest, canvas, template),
                               helpers=get_helpers(template))
    return rendered


@app.route('/<source>/object/<path:path>')
@set_toggle_model
def iiif_object(source, path):
    iiif = load_iiif(source, path)
    if iiif["type"] == "Collection":
        return render_template('collection.html', source=source, collection=iiif, helpers=get_helpers())
    else:
        return render_template('manifest.html', model=get_page_model(source, iiif), helpers=get_helpers())


def get_canvas_id(source, manifest_fragment, canvas_fragment):
    if source == WELLCOME:
        return f"https://{WELLCOME_HOST}/presentation/{manifest_fragment}/canvases/{canvas_fragment}"
    elif source == FRASER:
        return f"https://{FRASER_HOST}/presentation/{manifest_fragment}/canvases/{canvas_fragment}"
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
def canvas_url(source, manifest, canvas, canvas_template="canvas"):
    if source == WELLCOME:
        parts = canvas["id"].split("/")
        return f"/{WELLCOME}/{canvas_template}/{parts[-3]}/{parts[-1]}"
    elif source == FRASER:
        # tbc, assume same for the moment
        parts = canvas["id"].split("/")
        return f"/{FRASER}/{canvas_template}/{parts[-3]}/{parts[-1]}"
    elif source == RAW:
        if config["INTEGER_CANVASES"]:
            for idx, cvs in enumerate(manifest["items"]):
                if cvs["id"] == canvas["id"]:
                    return f"/{RAW}/{canvas_template}/{no_protocol(manifest['id'])}?canvas={idx}"
            raise ValueError(f"Can't find canvas {canvas['id']}")
        else:
            return f"/{RAW}/{canvas_template}/{no_protocol(manifest['id'])}?canvas={canvas['id']}"

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


# Expose utilities to template
def get_helpers(canvas_template="canvasv"):
    return {
        "canvas_template": canvas_template,
        "canvas_url": canvas_url,
        "manifest_url": manifest_url,
        "single_string": get_single_string,
        "strings": get_strings,
        "get_thumbnail": get_thumbnail,
        "get_static_image": get_static_image,
        "trim_model": trim_model
    }


def trim_model(model):
    # remove the manifest from the model and replace with its id
    # if the JS client wants the manifest it can ask for it
    trimmed = model.copy()
    if "manifest" in trimmed:
        del trimmed["manifest"]
    return trimmed


def get_page_model(source, manifest, canvas=None, canvas_template="canvasv"):
    page_model = {
        "source": source,
        "label": get_single_string(manifest, 'label'),
        "manifest": manifest,
        "manifest_id": manifest["id"],
        "total_canvases": len(manifest["items"]),
        "canvas": canvas,
        "prev_canvas": None,
        "next_canvas": None,
        "canvas_index": -1,
        "text_lines": get_text_lines(canvas),
        "canvas_url_list": []
    }
    if canvas is not None:
        for idx, cvs in enumerate(manifest["items"]):
            page_model["canvas_url_list"].append(canvas_url(source, manifest, cvs, canvas_template))
            if cvs["id"] == canvas["id"]:
                page_model["canvas_index"] = idx
                page_model["static_image"] = get_static_image(cvs)
                if idx > 0:
                    page_model["prev_canvas"] = manifest["items"][idx - 1]
                if idx+1 < len(manifest["items"]):
                    page_model["next_canvas"] = manifest["items"][idx + 1]

    return g.model | page_model


def no_protocol(old_url):
    new_url = old_url.removeprefix("https://")
    new_url = new_url.removeprefix("http://")
    return new_url


@app.route('/')
@set_toggle_model
def index():
    model = g.model
    model["manifests"] = []
    for manifest in samples.SAMPLES["items"]:
        manifest_id = manifest["id"]
        model_manifest = {
            "original": manifest_id,
            "label": get_single_string(manifest, "label"),
            "raw": url_for("iiif_object", source=RAW, path=no_protocol(manifest_id))
        }
        if manifest_id.startswith("https://iiif.wellcomecollection.org/presentation/"):
            model_manifest["internal"] = url_for("iiif_object", source=WELLCOME, path=manifest_id.split('/')[-1])
        elif manifest_id.startswith("https://iiif-dev.slf.digirati.io/presentation/"):
            model_manifest["internal"] = url_for("iiif_object", source=FRASER, path=manifest_id.split('/')[-1])
        else:
            model_manifest["internal"] = model_manifest["raw"]

        model["manifests"].append(model_manifest)

    return render_template('index.html', label='The Exploded Viewer', model=model, helpers=get_helpers())


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
    image_anno = next((anno for anno in painting_annos if anno["body"]["type"] == "Image"), None)
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
        img_svc_id = image_service.get("@id", None) or image_service.get("id", None)
        return {
            "id": f'{img_svc_id}/full/{useful_size["width"]},{useful_size["height"]}/0/default.jpg',
            "width": useful_size["width"],
            "height": useful_size["height"]
        }
    else:
        return {
            "id": image["id"],
            "width": image.get("width", None),
            "height": image.get("height", None),
        }
        # TODO we can optimise this further for smaller sizes.
        # Needs to work for level < 1: no !w,h unless profile supports it
        # return {
        #     "id": f'{image_service["id"]}/full/!{preferred_size},{preferred_size}/0/default.jpg',
        #     "width": None,
        #     "height": None
        # }


def get_image_service(image):
    if image is not None:
        services = image.get("service", [])
        image_service = next((s for s in services if has_image_service_type(s)), None)
        return image_service
    return None


def has_image_service_type(service):
    svc_type = service.get("@type", None) or service.get("type", None)
    if svc_type is None:
        return False
    return svc_type.startswith("ImageService")


@app.route("/toggles", methods=['POST', 'GET'])
@set_toggle_model
def toggles():
    # All handled in the @set_toggle_model decorator
    return render_template("toggles.html", model=g.model, helpers=get_helpers())


if __name__ == '__main__':
    app.run()
