"""Build the existing Django template into a standalone Render static site."""

import json
import os
import re
import shutil
from pathlib import Path


FRONTEND_DIR = Path(__file__).resolve().parent
REPOSITORY_DIR = FRONTEND_DIR.parent
OUTPUT_DIR = FRONTEND_DIR / "dist"
TEMPLATE = REPOSITORY_DIR / "webapp" / "templates" / "core" / "home.html"


def main() -> None:
    if OUTPUT_DIR.exists():
        shutil.rmtree(OUTPUT_DIR)
    OUTPUT_DIR.mkdir(parents=True)

    html = TEMPLATE.read_text(encoding="utf-8")
    html = html.replace("{% load static %}", "")
    html = html.replace("{% static 'core/style.css' %}", "/style.css")
    html = html.replace("{% static 'core/app.js' %}", "/app.js")
    html = html.replace("{% csrf_token %}", "")
    html = re.sub(r"{% for role in roles %}.*?{% endfor %}", "", html, flags=re.DOTALL)
    html = html.replace(
        "    <script src=\"/app.js\"></script>",
        "    <script src=\"/config.js\"></script>\n    <script src=\"/app.js\"></script>",
    )

    (OUTPUT_DIR / "index.html").write_text(html, encoding="utf-8")
    shutil.copy2(REPOSITORY_DIR / "webapp" / "static" / "core" / "style.css", OUTPUT_DIR / "style.css")
    shutil.copy2(REPOSITORY_DIR / "webapp" / "static" / "core" / "app.js", OUTPUT_DIR / "app.js")

    api_url = os.getenv(
        "SKILLBRIDGE_API_URL",
        "https://ai-skill-gap-analyzer-five.vercel.app",
    ).strip().rstrip("/")
    (OUTPUT_DIR / "config.js").write_text(
        f"window.SKILLBRIDGE_API_URL = {json.dumps(api_url)};\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
