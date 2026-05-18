"""Build static index.html from _posts/*.md.

Usage:
    pip install markdown
    python build_index.py

Reads:
    index.template.html  (with placeholders {{FEED}} a {{CURRENT_DATE}})
    _posts/*.md          (Jekyll-style front matter podporovan, ignoruje se)

Writes:
    index.html
"""

import html
import locale
import re
import sys
from datetime import datetime
from pathlib import Path

import markdown

ROOT = Path(__file__).parent
POSTS_DIR = ROOT / "_posts"
TEMPLATE = ROOT / "index.template.html"
OUTPUT = ROOT / "index.html"

CZ_MONTHS = [
    "ledna", "února", "března", "dubna", "května", "června",
    "července", "srpna", "září", "října", "listopadu", "prosince",
]
CZ_WEEKDAYS_SHORT = ["po", "út", "st", "čt", "pá", "so", "ne"]

FILENAME_DATE_RE = re.compile(r"^(\d{4})-(\d{2})-(\d{2})-")
FRONTMATTER_RE = re.compile(r"^---\s*\n.*?\n---\s*\n*", re.DOTALL)
HEADING_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*$", re.MULTILINE)
LETTER_RE = re.compile(r"^\s*<p[^>]*>\s*([^\s<])")


def format_cz_date(d: datetime) -> str:
    """e.g. 'po 18. května 2026'."""
    return f"{CZ_WEEKDAYS_SHORT[d.weekday()]} {d.day}. {CZ_MONTHS[d.month - 1]} {d.year}"


def strip_frontmatter(text: str) -> str:
    return FRONTMATTER_RE.sub("", text, count=1)


def split_title_and_body(content: str):
    """Find first markdown heading, treat its text as title, everything before
    as preamble (plain lines), everything after as body markdown.

    Returns (title, preamble_lines, body_md).
    """
    m = HEADING_RE.search(content)
    if not m:
        return None, [], content
    title = m.group(2).strip()
    before = content[: m.start()].strip()
    after = content[m.end():].lstrip("\n")
    preamble_lines = [ln.strip() for ln in before.split("\n") if ln.strip()] if before else []
    return title, preamble_lines, after


def render_post(md_path: Path, md_converter: markdown.Markdown) -> str:
    raw = md_path.read_text(encoding="utf-8")
    content = strip_frontmatter(raw)

    m = FILENAME_DATE_RE.match(md_path.name)
    if not m:
        raise ValueError(f"Soubor {md_path.name} nedodrzuje konvenci YYYY-MM-DD-*.md")
    year, month, day = (int(x) for x in m.groups())
    date_obj = datetime(year, month, day)
    date_str = format_cz_date(date_obj)

    title, preamble_lines, body_md = split_title_and_body(content)
    if title is None:
        # fallback: derive from filename
        title = md_path.stem.split("-", 3)[-1] if md_path.stem.count("-") >= 3 else md_path.stem

    md_converter.reset()
    body_html = md_converter.convert(body_md)

    # Drop cap on first paragraph, pouze kdyz zacina pismenem
    body_html = LETTER_RE.sub(
        lambda mm: mm.group(0).replace("<p", '<p class="has-drop-cap"', 1),
        body_html,
        count=1,
    )

    post_id = md_path.stem  # napr. "2026-05-18-post"

    preamble_html = ""
    if preamble_lines:
        ps = "".join(f"<p>{html.escape(line)}</p>" for line in preamble_lines)
        preamble_html = f'<div class="preamble">{ps}</div>'

    return (
        f'<article id="{html.escape(post_id)}">\n'
        f'  <div class="kicker" data-post-id="{html.escape(post_id)}" '
        f'title="Klikni pro zkopírování odkazu">{html.escape(date_str)}</div>\n'
        f'  {preamble_html}\n'
        f'  <h1 class="post-title">{html.escape(title)}</h1>\n'
        f'  <div class="post-content">{body_html}</div>\n'
        f'  <div style="text-align: center; color: var(--gold); margin-top: 40px;">'
        f'✦ &nbsp;&nbsp;&nbsp; ✦ &nbsp;&nbsp;&nbsp; ✦</div>\n'
        f'</article>'
    )


def main() -> int:
    if not TEMPLATE.exists():
        print(f"Chybi sablona: {TEMPLATE}", file=sys.stderr)
        return 1
    if not POSTS_DIR.is_dir():
        print(f"Chybi adresar: {POSTS_DIR}", file=sys.stderr)
        return 1

    md_converter = markdown.Markdown(
        extensions=["extra", "sane_lists", "smarty"],
        output_format="html5",
    )

    posts = sorted(
        (p for p in POSTS_DIR.glob("*.md") if FILENAME_DATE_RE.match(p.name)),
        key=lambda p: p.name,
        reverse=True,
    )

    articles_html = "\n\n".join(render_post(p, md_converter) for p in posts)

    template = TEMPLATE.read_text(encoding="utf-8")
    now = datetime.now()
    try:
        locale.setlocale(locale.LC_TIME, "en_GB.UTF-8")
    except locale.Error:
        pass
    current_date = now.strftime("%B %Y")

    out = template.replace("{{FEED}}", articles_html).replace(
        "{{CURRENT_DATE}}", current_date
    )
    OUTPUT.write_text(out, encoding="utf-8")
    print(f"Vygenerovano: {OUTPUT} ({len(posts)} prispevku)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
