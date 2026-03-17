import os
import json
import re
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, send_file, session
from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = "rekindled-secret-key"

client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

UPLOAD_FOLDER  = "uploads"
REPORTS_FOLDER = "reports"
os.makedirs(UPLOAD_FOLDER,  exist_ok=True)
os.makedirs(REPORTS_FOLDER, exist_ok=True)

LANGUAGES = ["English", "Turkish", "Spanish", "French", "Italian", "German", "Portuguese"]


# ── Parser ────────────────────────────────────────────────────
def parse_clippings(filepath):
    with open(filepath, "r", encoding="utf-8-sig") as f:
        content = f.read()

    entries  = content.split("==========")
    books    = {}
    skip_pat = re.compile(r'<.{0,3}You have reached the maximum number', re.IGNORECASE)

    for entry in entries:
        lines = [l.strip() for l in entry.strip().split("\n") if l.strip()]
        if len(lines) < 3:
            continue
        title     = lines[0]
        highlight = lines[-1]
        if skip_pat.search(highlight):
            continue
        books.setdefault(title, []).append(highlight)

    return books


# ── Genre detection ───────────────────────────────────────────
def detect_genre(title, highlights):
    sample = "\n".join([f"- {h}" for h in highlights[:3]])
    msg    = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=20,
        messages=[{"role": "user", "content": f"""Classify this book into exactly one of these genres:
Science, History & Politics, Economics & Finance, Technology & AI, Personal Growth & Self-Help, Philosophy & Spirituality, Literary Fiction, Science Fiction & Fantasy, Biography & Memoir, Poetry & Essays

Book title: {title}
Sample highlights:
{sample}

Reply with only the genre name, nothing else."""}]
    )
    return msg.content[0].text.strip()


# ── Report generation ─────────────────────────────────────────
def generate_report(title, highlights, genre, language):
    highlights_text = "\n".join([f"- {h}" for h in highlights])

    prose_instruction = f"Write the entire report in {language}. Write in flowing prose, no bullet points, no em dashes. Human and natural tone."
    structure         = "Use ## subheadings to organise the report into thematic sections. Use **bold** for key terms when they first appear."
    scale             = "Scale the length of the report to the number of highlights — do not pad or over-explain."

    prompts = {
        "Science":                     "Focus on explaining the core concepts and mechanisms clearly. Briefly clarify technical terms in plain language.",
        "History & Politics":          "Synthesise the key events, arguments and ideas into a coherent narrative. Briefly mention real historical context where useful.",
        "Economics & Finance":         "Explain the key concepts and arguments clearly. Use brief real-world examples or historical context where helpful.",
        "Technology & AI":             "Focus on the key ideas and their practical implications. Explain technical concepts accessibly.",
        "Personal Growth & Self-Help": "Focus on the actionable insights and core principles. Keep the tone direct, practical and motivating.",
        "Philosophy & Spirituality":   "Explore the ideas with depth and intellectual curiosity.",
        "Science Fiction & Fantasy":   "Note the world-building, thematic, and character elements that made these passages worth highlighting.",
        "Biography & Memoir":          "Capture the narrative arc of the person's life and ideas as reflected in these passages.",
        "Poetry & Essays":             "Preserve the highlights as they are and add light annotations on tone, feeling and resonance. Do not over-analyse. Keep it short.",
    }

    if genre == "Literary Fiction":
        prompt = f"""Here are my highlights from '{title}':\n\n{highlights_text}\n\nReturn each highlight exactly as it appears, one by one. Do not add any commentary. Just the highlights themselves."""
    else:
        genre_instruction = prompts.get(genre, prompts["History & Politics"])
        prompt = f"""Here are my highlights from '{title}':\n\n{highlights_text}\n\nWrite a Memory Report on these highlights. {structure} {genre_instruction} {scale} {prose_instruction}"""

    msg = client.messages.create(
        model="claude-opus-4-6",
        max_tokens=2048,
        messages=[{"role": "user", "content": prompt}]
    )
    return msg.content[0].text


# ── PDF generation ────────────────────────────────────────────
def generate_pdf(title, genre, highlight_count, date, report_text, language):
    from reportlab.lib.pagesizes import A4, landscape
    from reportlab.lib.units import mm
    from reportlab.lib.colors import HexColor
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.lib.enums import TA_JUSTIFY
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
    from reportlab.platypus.flowables import Flowable
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont

    pdfmetrics.registerFont(TTFont("Body",      "Inter/Inter-VariableFont_opsz,wght.ttf"))
    pdfmetrics.registerFont(TTFont("Body-Bold", "Inter/static/Inter_18pt-Bold.ttf"))

    BLUE  = HexColor('#1500FF')
    BLACK = HexColor('#111111')
    GRAY  = HexColor('#888888')
    LGRAY = HexColor('#DDDDDD')

    PAGE_W, PAGE_H = landscape(A4)
    LM, RM, TM, BM = 22*mm, 22*mm, 18*mm, 16*mm
    body_w = PAGE_W - LM - RM

    def parse_title_author(raw):
        match = re.match(r'^(.*?)\s*\(([^)]+)\)\s*$', raw.strip())
        if match:
            return match.group(1).strip(), match.group(2).strip()
        return raw.strip(), None

    book_title, author = parse_title_author(title)
    short_title        = " ".join(book_title.split()[:4])
    safe               = re.sub(r'[^\w\s-]', '', book_title).strip().replace(' ', '_')[:40]
    out_path           = f"reports/{safe}_Memory_Report.pdf"

    class HeaderBlock(Flowable):
        def __init__(self):
            super().__init__()
            self.width  = body_w
            self.height = 58 * mm

        def draw(self):
            c = self.canv
            w = self.width
            h = self.height
            top_y = h - 2
            c.setFont("Body", 7.5)
            c.setFillColor(BLUE)
            c.drawString(0, top_y, genre.upper())
            c.setFillColor(GRAY)
            c.drawCentredString(w / 2, top_y, "REKINDLED")
            c.drawRightString(w, top_y, date)
            rule_y = top_y - 5*mm
            c.setStrokeColor(BLACK)
            c.setLineWidth(0.4)
            c.line(0, rule_y, w, rule_y)
            title_y = rule_y - 11*mm
            c.setFont("Body-Bold", 32)
            c.setFillColor(BLACK)
            title_w = c.stringWidth(book_title, "Body-Bold", 32)
            if title_w > w:
                words = book_title.split()
                mid   = len(words) // 2
                lines = [" ".join(words[:mid]), " ".join(words[mid:])]
            else:
                lines = [book_title]
            for line in lines:
                c.drawString(0, title_y, line)
                title_y -= 38
            if author:
                c.setFont("Body", 12)
                c.setFillColor(GRAY)
                c.drawString(0, title_y - 1*mm, author)
                title_y = title_y - 1*mm - 8*mm
            blue_y = title_y - 2
            c.setStrokeColor(BLUE)
            c.setLineWidth(2)
            c.line(0, blue_y, w, blue_y)
            c.setFont("Body", 8)
            c.setFillColor(GRAY)
            c.drawString(0, blue_y - 6*mm, f"{highlight_count} highlights")

    class SubheadingBlock(Flowable):
        def __init__(self, text):
            super().__init__()
            self.text   = text
            self.width  = body_w
            self.height = 14 * mm

        def draw(self):
            c      = self.canv
            text_y = self.height - 10
            c.setFont("Body-Bold", 12)
            c.setFillColor(BLACK)
            c.drawString(0, text_y, self.text)
            rule_y = text_y - 3.5*mm
            c.setStrokeColor(BLUE)
            c.setLineWidth(0.8)
            c.line(0, rule_y, self.width, rule_y)

    def on_first_page(canvas, doc):
        canvas.saveState()
        canvas.setStrokeColor(LGRAY)
        canvas.setLineWidth(0.4)
        canvas.line(LM, BM+2*mm, PAGE_W-RM, BM+2*mm)
        canvas.setFont("Body", 7.5)
        canvas.setFillColor(GRAY)
        canvas.drawCentredString(PAGE_W/2, BM-2*mm, str(doc.page))
        canvas.restoreState()

    def on_later_pages(canvas, doc):
        canvas.saveState()
        top_y = PAGE_H - TM + 3*mm
        canvas.setFont("Body", 7.5)
        canvas.setFillColor(GRAY)
        canvas.drawString(LM, top_y, short_title.upper())
        canvas.drawCentredString(PAGE_W/2, top_y, "REKINDLED")
        canvas.setStrokeColor(LGRAY)
        canvas.setLineWidth(0.4)
        canvas.line(LM, top_y-4*mm, PAGE_W-RM, top_y-4*mm)
        canvas.setStrokeColor(LGRAY)
        canvas.line(LM, BM+2*mm, PAGE_W-RM, BM+2*mm)
        canvas.setFont("Body", 7.5)
        canvas.setFillColor(GRAY)
        canvas.drawCentredString(PAGE_W/2, BM-2*mm, str(doc.page))
        canvas.restoreState()

    body_style = ParagraphStyle("body", fontName="Body", fontSize=10.5,
                                textColor=BLACK, leading=17, spaceAfter=4*mm,
                                alignment=TA_JUSTIFY)

    doc   = SimpleDocTemplate(out_path, pagesize=landscape(A4),
                               leftMargin=LM, rightMargin=RM,
                               topMargin=TM+8*mm, bottomMargin=BM+8*mm)
    story = [HeaderBlock(), Spacer(1, 5*mm)]

    for para in [p.strip() for p in report_text.split('\n') if p.strip()]:
        if para.startswith('# '):
            continue
        elif para.startswith('## '):
            story.append(Spacer(1, 3*mm))
            story.append(SubheadingBlock(para[3:].strip()))
            story.append(Spacer(1, 2*mm))
        else:
            clean = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', para)
            story.append(Paragraph(clean, body_style))

    doc.build(story, onFirstPage=on_first_page, onLaterPages=on_later_pages)
    return out_path


# ── Routes ────────────────────────────────────────────────────
@app.route("/", methods=["GET", "POST"])
def upload():
    if request.method == "POST":
        file = request.files.get("clippings")
        if not file or file.filename == "":
            return render_template("upload.html", error="Please select a file.")
        filepath = os.path.join(UPLOAD_FOLDER, "clippings.txt")
        file.save(filepath)
        books = parse_clippings(filepath)
        books_path = os.path.join(UPLOAD_FOLDER, "books.json")
        with open(books_path, "w", encoding="utf-8") as f:
            json.dump(books, f, ensure_ascii=False)
        session["books_ready"] = True
        return redirect(url_for("select"))
    return render_template("upload.html")


@app.route("/select", methods=["GET", "POST"])
def select():
    if not session.get("books_ready"):
        return redirect(url_for("upload"))
    books_path = os.path.join(UPLOAD_FOLDER, "books.json")
    if not os.path.exists(books_path):
        return redirect(url_for("upload"))
    with open(books_path, "r", encoding="utf-8") as f:
        books = json.load(f)
    if not books:
        return redirect(url_for("upload"))
    if request.method == "POST":
        title      = request.form.get("title")
        language   = request.form.get("language")
        highlights = books[title]
        genre      = detect_genre(title, highlights)
        report     = generate_report(title, highlights, genre, language)
        date       = datetime.now().strftime("%B %d, %Y")
        pdf_path   = generate_pdf(title, genre, len(highlights), date, report, language)
        session["pdf_path"]   = pdf_path
        session["book_title"] = title
        return redirect(url_for("done"))
    return render_template("select.html", books=list(books.keys()), languages=LANGUAGES)


@app.route("/done")
def done():
    title = session.get("book_title", "Your book")
    return render_template("done.html", title=title)


@app.route("/download")
def download():
    pdf_path = session.get("pdf_path")
    if not pdf_path or not os.path.exists(pdf_path):
        return redirect(url_for("upload"))
    return send_file(pdf_path, as_attachment=True)


if __name__ == "__main__":
        app.run(debug=True, port=5001)



# Every time you want to use it, you do two things in the VS Code terminal. 
# First activate the venv with source venv/bin/activate, then run python app.py. 
# Then open your browser and go to http://127.0.0.1:5000. That's it.    