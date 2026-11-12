# Build the coursework PDF from report.md (not part of the statistical analysis).
#
#   python coursework/build_report.py --id 12345678
#
# Steps: count the words of the main text, convert the Markdown to HTML, append
# analysis.py as the code appendix, and print the HTML to PDF with headless Edge/Chrome.

import argparse
import re
import subprocess
import sys
from pathlib import Path

import markdown
from pygments import highlight
from pygments.formatters import HtmlFormatter
from pygments.lexers import PythonLexer

HERE = Path(__file__).resolve().parent
BROWSERS = [
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
]

CSS = """
@page { size: A4; margin: 20mm 19mm 20mm 19mm;
        @bottom-center { content: counter(page); font: 9pt Calibri, Arial, sans-serif; color: #555; } }
* { box-sizing: border-box; }
body { font: 10.5pt/1.42 Calibri, "Segoe UI", Arial, sans-serif; color: #111; margin: 0; }
h1 { font-size: 16pt; margin: 0 0 2pt; }
h2 { font-size: 12.5pt; margin: 13pt 0 4pt; break-after: avoid; }
h3 { font-size: 11pt; margin: 10pt 0 3pt; break-after: avoid; }
p { margin: 0 0 6pt; text-align: justify; }
.meta { color: #333; margin-bottom: 8pt; text-align: left; }
.eq { text-align: center; margin: 5pt 0 7pt; font-family: "Cambria Math", Cambria, "Times New Roman", serif; font-size: 11pt; }
table { border-collapse: collapse; margin: 3pt auto 8pt; font-size: 9pt; break-inside: avoid; }
th, td { padding: 2.2pt 7pt; text-align: right; }
th:first-child, td:first-child { text-align: left; }
thead th { border-top: 1.2pt solid #111; border-bottom: 0.7pt solid #111; }
tbody tr:last-child td { border-bottom: 1.2pt solid #111; }
.caption { font-size: 9pt; color: #222; text-align: left; margin: 6pt 0 2pt; break-after: avoid; }
figure { margin: 6pt 0 8pt; text-align: center; break-inside: avoid; }
figure img { max-width: 100%; }
figcaption { font-size: 9pt; color: #222; text-align: left; margin-top: 2pt; }
.refs p { text-align: left; padding-left: 16pt; text-indent: -16pt; font-size: 9.5pt; }
.appendix { break-before: page; }
.codehilite { font-size: 7.6pt; line-height: 1.25; }
.codehilite pre { white-space: pre-wrap; word-break: break-word; margin: 0;
                  font-family: Consolas, "Courier New", monospace; }
code { font-family: Consolas, "Courier New", monospace; font-size: 9.5pt; }
"""


def count_words(md_text):
    """Words in the main text: everything before the references, without
    tables, table/figure captions and figures (these are excluded by the brief)."""
    body = re.split(r"^## References", md_text, flags=re.M)[0]
    body = re.sub(r"<figure>.*?</figure>", " ", body, flags=re.S)
    body = re.sub(r'<p class="(caption|meta)">.*?</p>', " ", body, flags=re.S)
    body = "\n".join(line for line in body.splitlines() if not line.lstrip().startswith("|"))
    body = re.sub(r"<[^>]+>", " ", body)            # remaining HTML tags
    body = re.sub(r"[#*_`]", "", body)              # Markdown symbols
    body = re.sub(r"&[a-z]+;", "x", body)           # HTML entities count as one character
    return sum(1 for token in body.split() if re.search(r"[A-Za-z0-9]", token))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--id", default="STUDENTID", help="student ID number")
    args = parser.parse_args()

    md_text = (HERE / "report.md").read_text(encoding="utf-8")
    words = count_words(md_text)
    print(f"Word count of the main text: {words}")
    md_text = md_text.replace("{{STUDENT_ID}}", args.id).replace("{{WORD_COUNT}}", str(words))

    body = markdown.markdown(md_text, extensions=["tables", "md_in_html", "sane_lists"])

    formatter = HtmlFormatter(style="default", nowrap=False, cssclass="codehilite")
    code = (HERE / "analysis.py").read_text(encoding="utf-8")
    appendix = ('<div class="appendix"><h2>Appendix: Python code</h2>'
                '<p>All results, tables and figures in this report were produced by the script below '
                '(Python 3.12 with pandas, NumPy, SciPy, statsmodels, scikit-learn, matplotlib and seaborn).</p>'
                + highlight(code, PythonLexer(), formatter) + "</div>")

    html = (f'<!doctype html><html lang="en"><head><meta charset="utf-8">'
            f"<title>{args.id}_DATA70121</title><style>{CSS}{formatter.get_style_defs('.codehilite')}"
            f".codehilite {{ background: none; }}</style></head><body>{body}{appendix}</body></html>")
    html_path = HERE / "report.html"
    html_path.write_text(html, encoding="utf-8")

    pdf_path = HERE / f"{args.id}_DATA70121.pdf"
    browser = next((b for b in BROWSERS if Path(b).exists()), None)
    if browser is None:
        sys.exit("No Edge/Chrome found: open report.html and print it to PDF by hand.")
    subprocess.run([browser, "--headless", "--disable-gpu", "--no-pdf-header-footer",
                    f"--print-to-pdf={pdf_path}", html_path.as_uri()], check=True)
    print("Written:", pdf_path)


if __name__ == "__main__":
    main()
