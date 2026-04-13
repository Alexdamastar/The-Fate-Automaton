import json
from pathlib import Path


def build_html(payload):
    base = Path(__file__).parent
    html = (base / "app.html").read_text(encoding="utf-8")
    css = (base / "styles.css").read_text(encoding="utf-8")
    js = (base / "app.js").read_text(encoding="utf-8")

    js = js.replace("__DATA__", json.dumps(payload, indent=2))
    html = html.replace("__STYLES__", css)
    html = html.replace("__SCRIPT__", js)
    return html
