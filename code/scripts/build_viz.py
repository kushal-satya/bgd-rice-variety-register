"""Inject 05_output/final/viz_data.json into the page template.

Writes two files:
- 05_output/final/rice_register.html             page body for the claude.ai artifact (the host adds the HTML skeleton)
- 05_output/final/rice_register_standalone.html  complete HTML document: opens from disk, e-mail or any web server
Both are fully self-contained: data embedded, no external scripts, fonts or requests."""
import pathlib

R = pathlib.Path(__file__).resolve().parents[1]
data = (R / "05_output/final/viz_data.json").read_text(encoding="utf-8").replace("</", r"<\/")
html = (R / "scripts/viz_template.html").read_text(encoding="utf-8").replace("__DATA__", data)
out = R / "05_output/final/rice_register.html"
out.write_text(html, encoding="utf-8")
print(out, round(len(html.encode()) / 1024), "KB")

head = "\n".join([
    "<!doctype html>",
    '<html lang="en">',
    "<head>",
    '<meta charset="utf-8">',
    '<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">',
])
style_end = html.index("</style>") + len("</style>")
standalone = "\n".join([head, html[:style_end], "</head>", "<body>", html[style_end:], "</body>", "</html>", ""])
so = R / "05_output/final/rice_register_standalone.html"
so.write_text(standalone, encoding="utf-8")
print(so, round(len(standalone.encode()) / 1024), "KB")
