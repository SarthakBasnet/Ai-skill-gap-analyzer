"""Build the static-site handoff to the same-origin Django application."""

import json
import os
import shutil
from html import escape
from pathlib import Path
from urllib.parse import urlsplit


FRONTEND_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = FRONTEND_DIR / "dist"


def main() -> None:
    if OUTPUT_DIR.exists():
        shutil.rmtree(OUTPUT_DIR)
    OUTPUT_DIR.mkdir(parents=True)

    default_app_url = "https://ai-skill-gap-analyzer-five.vercel.app"
    app_url = os.getenv("SKILLBRIDGE_API_URL", default_app_url).strip().rstrip("/") or default_app_url
    parsed_url = urlsplit(app_url)
    if parsed_url.scheme not in {"http", "https"} or not parsed_url.netloc:
        raise ValueError("SKILLBRIDGE_API_URL must be an absolute HTTP or HTTPS app URL.")
    safe_url = escape(app_url, quote=True)
    script_url = json.dumps(app_url)
    redirect_page = f'''<!doctype html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <meta name="robots" content="noindex">
    <meta http-equiv="refresh" content="0;url={safe_url}/">
    <title>Opening SkillBridge…</title>
    <style>
        :root {{ color-scheme: light; font-family: "Trebuchet MS", sans-serif; color: #2b2a25; background: #f7f5ed; }}
        body {{ align-items: center; display: flex; justify-content: center; margin: 0; min-height: 100vh; padding: 24px; }}
        main {{ background: #fffdf8; border-top: 3px solid #596b3d; max-width: 420px; padding: 36px; text-align: center; }}
        h1 {{ font-family: Georgia, serif; font-size: 2rem; }}
        p {{ color: #5e5b50; line-height: 1.6; }}
        a {{ background: #596b3d; color: #fffdf8; display: inline-block; font-weight: 700; margin-top: 12px; padding: 13px 18px; text-decoration: none; }}
    </style>
</head>
<body>
    <main>
        <h1>Opening SkillBridge</h1>
        <p>Taking you to the secure SkillBridge app.</p>
        <a href="{safe_url}/">Continue to SkillBridge</a>
    </main>
    <script>window.location.replace({script_url} + "/");</script>
</body>
</html>
'''
    (OUTPUT_DIR / "index.html").write_text(redirect_page, encoding="utf-8")


if __name__ == "__main__":
    main()
