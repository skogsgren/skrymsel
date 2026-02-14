from dataclasses import dataclass
import json
from pathlib import Path
import shutil
import sys
from typing import Any

from frontmatter import Frontmatter
from markdown import markdown
import jinja2

TEMPLATES_DIR = Path("./templates")
STATIC_DIR = Path("./static")
PINS_DIR = Path("./pins")


@dataclass
class Pin:
    slug: str
    title: str
    description: str
    lat: float
    lon: float
    body_html: str
    popup_image: str | None


def parse_pin_file(p: Path) -> Pin:
    post = Frontmatter.read_file(p)
    attr = post["attributes"]
    return Pin(
        slug=p.stem,
        title=str(attr["title"]),
        description=str(attr["description"]),
        lat=float(attr["lat"]),
        lon=float(attr["lon"]),
        body_html=markdown(post["body"]),
        popup_image=str(attr["popup_image"]) if "popup_image" in attr else None,
    )


def pin_to_json(pin: Pin) -> dict[str, Any]:
    return {
        "slug": pin.slug,
        "title": pin.title,
        "description": pin.description,
        "lat": pin.lat,
        "lon": pin.lon,
        "url": f"/pins/{pin.slug}/",
        "popup_image": pin.popup_image,
    }


def copy_static_assets(serve_dir: Path) -> None:
    out_static = serve_dir / "static"
    out_static.mkdir(parents=True, exist_ok=True)
    for path in STATIC_DIR.rglob("*"):
        if path.is_dir():
            continue
        rel = path.relative_to(STATIC_DIR)
        target = out_static / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, target)


def render_pin_page(env: jinja2.Environment, serve_dir: Path, pin: Pin) -> None:
    template = env.get_template("pin_article.html")
    pin_dir = serve_dir / "pins" / pin.slug
    pin_dir.mkdir(parents=True, exist_ok=True)
    (pin_dir / "index.html").write_text(
        template.render(pin=pin),
        encoding="utf-8",
    )


def main(serve_dir: Path) -> int:
    serve_dir.mkdir(parents=True, exist_ok=True)
    env = jinja2.Environment(
        loader=jinja2.FileSystemLoader(TEMPLATES_DIR),
        autoescape=jinja2.select_autoescape(["html"]),
    )

    pins: list[Pin] = []
    if PINS_DIR.exists():
        for p in sorted(PINS_DIR.iterdir()):
            if p.suffix == ".md":
                pins.append(parse_pin_file(p))

    for pin in pins:
        render_pin_page(env, serve_dir, pin)

    index_template = env.get_template("index.html")
    (serve_dir / "index.html").write_text(
        index_template.render(
            pins=pins,
            pins_json=json.dumps([pin_to_json(pin) for pin in pins]),
        ),
        encoding="utf-8",
    )
    copy_static_assets(serve_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(Path(sys.argv[1]) if len(sys.argv) > 1 else Path("./serve")))
