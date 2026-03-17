import json
import re
import os
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.units import mm
from reportlab.lib.colors import HexColor
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_JUSTIFY, TA_LEFT
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.platypus.flowables import Flowable
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# ── Fonts ─────────────────────────────────────────────────────
pdfmetrics.registerFont(TTFont("Body",        "Inter/Inter-VariableFont_opsz,wght.ttf"))
pdfmetrics.registerFont(TTFont("Body-Bold",   "Inter/static/Inter_18pt-Bold.ttf"))
pdfmetrics.registerFont(TTFont("Body-Italic", "Inter/Inter-Italic-VariableFont_opsz,wght.ttf"))

# ── Design tokens ─────────────────────────────────────────────
BLUE  = HexColor('#1500FF')
BLACK = HexColor('#111111')
GRAY  = HexColor('#888888')
LGRAY = HexColor('#DDDDDD')

PAGE_W, PAGE_H = landscape(A4)
LM = 22 * mm
RM = 22 * mm
TM = 18 * mm
BM = 16 * mm


# ── Parse author from title ───────────────────────────────────
def parse_title_author(raw):
    match = re.match(r'^(.*?)\s*\(([^)]+)\)\s*$', raw.strip())
    if match:
        return match.group(1).strip(), match.group(2).strip()
    return raw.strip(), None


# ── Styles ────────────────────────────────────────────────────
def make_styles():
    return {
        "meta": ParagraphStyle(
            "meta",
            fontName="Body",
            fontSize=7.5,
            textColor=GRAY,
            leading=12,
            alignment=TA_LEFT,
        ),
        "title": ParagraphStyle(
            "title",
            fontName="Body-Bold",
            fontSize=32,
            textColor=BLACK,
            leading=36,
            spaceAfter=1 * mm,
            alignment=TA_LEFT,
        ),
        "author": ParagraphStyle(
            "author",
            fontName="Body",
            fontSize=12,
            textColor=GRAY,
            leading=16,
            spaceAfter=2 * mm,
            alignment=TA_LEFT,
        ),
        "highlight_count": ParagraphStyle(
            "highlight_count",
            fontName="Body",
            fontSize=8,
            textColor=GRAY,
            leading=12,
            spaceBefore=3 * mm,
            spaceAfter=6 * mm,
        ),
        "h2": ParagraphStyle(
            "h2",
            fontName="Body-Bold",
            fontSize=12,
            textColor=BLACK,
            leading=17,
            spaceBefore=7 * mm,
            spaceAfter=1 * mm,
            alignment=TA_LEFT,
        ),
        "body": ParagraphStyle(
            "body",
            fontName="Body",
            fontSize=10.5,
            textColor=BLACK,
            leading=17,
            spaceAfter=4 * mm,
            alignment=TA_JUSTIFY,
        ),
    }


# ── Header flowable ───────────────────────────────────────────
class HeaderBlock(Flowable):
    def __init__(self, title, author, genre, highlight_count, date_generated, width):
        super().__init__()
        self.title           = title
        self.author          = author
        self.genre           = genre
        self.highlight_count = highlight_count
        self.date_generated  = date_generated
        self.width           = width
        self.height          = 58 * mm

    def draw(self):
        c = self.canv
        w = self.width
        h = self.height

        # Top row: genre | REKINDLED | date
        top_y = h - 2
        c.setFont("Body", 7.5)
        c.setFillColor(BLUE)
        c.drawString(0, top_y, self.genre.upper())
        c.setFillColor(GRAY)
        c.drawCentredString(w / 2, top_y, "REKINDLED")
        c.drawRightString(w, top_y, self.date_generated)

        # Thin black rule
        rule_y = top_y - 5 * mm
        c.setStrokeColor(BLACK)
        c.setLineWidth(0.4)
        c.line(0, rule_y, w, rule_y)

        # Large title
        title_y = rule_y - 11 * mm
        c.setFont("Body-Bold", 32)
        c.setFillColor(BLACK)

        title_w = c.stringWidth(self.title, "Body-Bold", 32)
        if title_w > w:
            words = self.title.split()
            mid   = len(words) // 2
            lines = [" ".join(words[:mid]), " ".join(words[mid:])]
        else:
            lines = [self.title]

        for line in lines:
            c.drawString(0, title_y, line)
            title_y -= 38

        # Author name beneath title
        if self.author:
            author_y = title_y - 1 * mm
            c.setFont("Body", 12)
            c.setFillColor(GRAY)
            c.drawString(0, author_y, self.author)
            title_y = author_y - 8 * mm

        # Thick blue rule
        blue_y = title_y - 2
        c.setStrokeColor(BLUE)
        c.setLineWidth(2)
        c.line(0, blue_y, w, blue_y)

        # Highlight count
        c.setFont("Body", 8)
        c.setFillColor(GRAY)
        c.drawString(0, blue_y - 6 * mm, f"{self.highlight_count} highlights")


# ── Subheading with blue rule ─────────────────────────────────
class SubheadingBlock(Flowable):
    def __init__(self, text, width):
        super().__init__()
        self.text   = text
        self.width  = width
        self.height = 14 * mm

    def draw(self):
        c = self.canv
        text_y = self.height - 10
        c.setFont("Body-Bold", 12)
        c.setFillColor(BLACK)
        c.drawString(0, text_y, self.text)

        rule_y = text_y - 3.5 * mm
        c.setStrokeColor(BLUE)
        c.setLineWidth(0.8)
        c.line(0, rule_y, self.width, rule_y)


# ── Continuation page header ──────────────────────────────────
def draw_continuation_header(canvas, doc, short_title):
    canvas.saveState()
    top_y = PAGE_H - TM + 3 * mm

    canvas.setFont("Body", 7.5)
    canvas.setFillColor(GRAY)
    canvas.drawString(LM, top_y, short_title.upper())
    canvas.drawCentredString(PAGE_W / 2, top_y, "REKINDLED")

    canvas.setStrokeColor(LGRAY)
    canvas.setLineWidth(0.4)
    canvas.line(LM, top_y - 4 * mm, PAGE_W - RM, top_y - 4 * mm)
    canvas.restoreState()


# ── Footer ────────────────────────────────────────────────────
def draw_footer(canvas, doc):
    canvas.saveState()
    canvas.setStrokeColor(LGRAY)
    canvas.setLineWidth(0.4)
    canvas.line(LM, BM + 2 * mm, PAGE_W - RM, BM + 2 * mm)
    canvas.setFont("Body", 7.5)
    canvas.setFillColor(GRAY)
    canvas.drawCentredString(PAGE_W / 2, BM - 2 * mm, str(doc.page))
    canvas.restoreState()


# ── Markdown parser ───────────────────────────────────────────
def parse_report(text, styles, body_w):
    flowables  = []
    paragraphs = [p.strip() for p in text.split('\n') if p.strip()]

    for para in paragraphs:
        if para.startswith('# '):
            continue
        elif para.startswith('## '):
            clean = para[3:].strip()
            flowables.append(Spacer(1, 3 * mm))
            flowables.append(SubheadingBlock(clean, body_w))
            flowables.append(Spacer(1, 2 * mm))
        else:
            clean = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', para)
            flowables.append(Paragraph(clean, styles["body"]))

    return flowables


# ── Main ──────────────────────────────────────────────────────
def generate_pdf(report_path="report.json"):
    with open(report_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    raw_title = data["book_title"]
    genre     = data["genre"]
    count     = data["highlight_count"]
    date      = data["date_generated"]
    text      = data["report_text"]

    title, author = parse_title_author(raw_title)
    short_title   = " ".join(title.split()[:4])


    safe     = re.sub(r'[^\w\s-]', '', title).strip().replace(' ', '_')[:40]
    os.makedirs("reports", exist_ok=True)
    out_path = f"reports/{safe}_Memory_Report.pdf"

    body_w = PAGE_W - LM - RM

    doc = SimpleDocTemplate(
        out_path,
        pagesize=landscape(A4),
        leftMargin=LM,
        rightMargin=RM,
        topMargin=TM + 8 * mm,
        bottomMargin=BM + 8 * mm,
        title=f"Memory Report — {title}",
        author="Rekindled",
    )

    styles = make_styles()
    story  = []

    story.append(HeaderBlock(title, author, genre, count, date, body_w))
    story.append(Spacer(1, 5 * mm))
    story.extend(parse_report(text, styles, body_w))

    def on_first_page(canvas, doc):
        draw_footer(canvas, doc)

    def on_later_pages(canvas, doc):
        draw_continuation_header(canvas, doc, short_title)
        draw_footer(canvas, doc)

    doc.build(story, onFirstPage=on_first_page, onLaterPages=on_later_pages)
    print(f"\nPDF saved: {out_path}")


if __name__ == "__main__":
    generate_pdf()