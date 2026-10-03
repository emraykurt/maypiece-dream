"""Builds a game's hosted privacy page from the game's docs/privacy-policy.md (the game repo owns the text).

Takes the "## Türkçe" and "## English" sections (everything after them, e.g. update notes, is skipped) and renders the
small Markdown subset those files use: ### headings, paragraphs, "-" lists, **bold**, bare https links.
    python tools/md2page.py C:/Dev/EtiketUstasi/docs/privacy-policy.md etiket-ustasi/gizlilik.html "Etiket Ustası"
"""
import html
import re
import sys


def inline(text):
    t = html.escape(text, quote=False)
    t = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", t)
    t = re.sub(r"(?<![\"=])(https?://[^\s<)]+[^\s<).,])", r'<a href="\1">\1</a>', t)
    t = re.sub(r"\b([\w.+-]+@[\w-]+\.[\w.]+)\b", r'<a href="mailto:\1">\1</a>', t)
    return t


def render(lines):
    out, para, items = [], [], []

    def flush():
        if para:
            out.append("<p>" + inline(" ".join(para)) + "</p>")
            para.clear()
        if items:
            out.append("<ul>\n" + "\n".join("<li>" + inline(i) + "</li>" for i in items) + "\n</ul>")
            items.clear()

    for raw in lines:
        line = raw.rstrip()
        if not line.strip():
            flush()
        elif line.startswith("### "):
            flush()
            out.append("<h3>" + inline(line[4:]) + "</h3>")
        elif line.lstrip().startswith("- "):
            if para:
                flush()
            items.append(line.lstrip()[2:])
        elif items and raw.startswith("  "):
            items[-1] += " " + line.strip()
        else:
            if items:
                flush()
            para.append(line.strip())
    flush()
    return "\n".join(out)


def section(text, title):
    m = re.search(r"^## " + re.escape(title) + r"\s*$(.*?)(?=^## |\Z)", text, re.S | re.M)
    if not m:
        sys.exit("section not found: " + title)
    body = [l for l in m.group(1).strip().splitlines() if l.strip() != "---"]
    meta = [l for l in body if l.startswith("**") and ":**" in l]
    rest = [l for l in body if l not in meta]
    meta_html = "<br>\n".join(inline(l) for l in meta)
    return meta_html, render(rest)


def main(src, dst, app):
    text = open(src, encoding="utf-8").read()
    tr_meta, tr_body = section(text, "Türkçe")
    en_meta, en_body = section(text, "English")
    page = f"""<!doctype html>
<html lang="tr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(app)} Gizlilik</title>
<link rel="stylesheet" href="../style.css">
</head>
<body>
<main>
<h1>{html.escape(app)} - Gizlilik Politikası</h1>
<p class="meta">{tr_meta}</p>
<p class="lang"><a href="#tr">Türkçe</a> <a href="#en">English</a></p>

<section id="tr">
{tr_body}
</section>

<section id="en">
<h2>{html.escape(app)} - Privacy Policy</h2>
<p class="meta">{en_meta}</p>
{en_body}
</section>

<footer><a href="../index.html">Maypiece Dream</a></footer>
</main>
</body>
</html>
"""
    open(dst, "w", encoding="utf-8", newline="\n").write(page)
    print("wrote", dst, len(page), "bytes")


if __name__ == "__main__":
    main(*sys.argv[1:4])
