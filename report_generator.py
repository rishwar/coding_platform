"""
PDF Report Generator for CodeRound Interview Platform.
Generates a professional candidate assessment report using ReportLab.
"""
import io
from datetime import datetime

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, KeepTogether, PageBreak
)
from reportlab.platypus.flowables import Flowable


# ── Brand colours ─────────────────────────────────────────────────────────────
ORANGE      = colors.HexColor("#E86C2C")
DARK        = colors.HexColor("#1C1917")
CREAM       = colors.HexColor("#F0EDE6")
CARD_BG     = colors.HexColor("#FAFAF8")
BORDER      = colors.HexColor("#E8E4DC")
GREEN       = colors.HexColor("#16A34A")
RED         = colors.HexColor("#DC2626")
GREY        = colors.HexColor("#6B6560")
LIGHT_GREEN = colors.HexColor("#F0FDF4")
LIGHT_RED   = colors.HexColor("#FEF2F2")
BLUE        = colors.HexColor("#3B82F6")
AMBER       = colors.HexColor("#D97706")

W, H = A4   # 595 x 842 pt


# ── Custom horizontal rule ────────────────────────────────────────────────────
class OrangeLine(Flowable):
    def __init__(self, width=None, thickness=2):
        Flowable.__init__(self)
        self.line_width = width
        self.thickness  = thickness

    def draw(self):
        w = self.line_width or self._frame._width
        self.canv.setStrokeColor(ORANGE)
        self.canv.setLineWidth(self.thickness)
        self.canv.line(0, 0, w, 0)

    def wrap(self, availWidth, availHeight):
        self.line_width = self.line_width or availWidth
        return (self.line_width, self.thickness + 2)


# ── Style helpers ─────────────────────────────────────────────────────────────
def _style(**kw):
    base = getSampleStyleSheet()["Normal"]
    s = ParagraphStyle("custom", parent=base)
    for k, v in kw.items():
        setattr(s, k, v)
    return s


TITLE_STYLE    = _style(fontSize=26, fontName="Helvetica-Bold", textColor=CREAM,
                         leading=30, spaceAfter=4)
SUBTITLE_STYLE = _style(fontSize=11, fontName="Helvetica", textColor=colors.HexColor("#A8A39C"),
                         leading=14)
LOGO_STYLE     = _style(fontSize=20, fontName="Helvetica-Bold", textColor=CREAM, leading=24)

H1_STYLE       = _style(fontSize=13, fontName="Helvetica-Bold", textColor=DARK,
                         leading=16, spaceBefore=14, spaceAfter=6)
H2_STYLE       = _style(fontSize=10, fontName="Helvetica-Bold", textColor=GREY,
                         leading=13, spaceBefore=10, spaceAfter=4,
                         textTransform="uppercase", letterSpacing=0.8)
BODY_STYLE     = _style(fontSize=9.5, fontName="Helvetica", textColor=DARK, leading=14)
SMALL_STYLE    = _style(fontSize=8.5, fontName="Helvetica", textColor=GREY, leading=12)
CODE_STYLE     = _style(fontSize=8, fontName="Courier", textColor=colors.HexColor("#D0C8C0"),
                         backColor=DARK, leading=12, leftIndent=8, rightIndent=8,
                         spaceBefore=4, spaceAfter=4)
LABEL_STYLE    = _style(fontSize=8, fontName="Helvetica-Bold", textColor=GREY,
                         leading=11, textTransform="uppercase", letterSpacing=0.6)
RESULT_OK_STYLE = _style(fontSize=9, fontName="Helvetica-Bold", textColor=GREEN, leading=12)
RESULT_NO_STYLE = _style(fontSize=9, fontName="Helvetica-Bold", textColor=RED,   leading=12)


# ── Diff / category colours ───────────────────────────────────────────────────
DIFF_COLOR = {"Easy": GREEN, "Medium": AMBER, "Hard": RED}
CAT_COLOR  = {"SQL": BLUE, "Python": GREEN, "PySpark": ORANGE}


def _diff_color(d): return DIFF_COLOR.get(d, GREY)
def _cat_color(c):  return CAT_COLOR.get(c, GREY)


# ── Page template (header/footer on every page) ────────────────────────────────
def _make_page_fn(candidate_name, generated_at):
    def on_page(canvas, doc):
        canvas.saveState()
        # Top stripe
        canvas.setFillColor(DARK)
        canvas.rect(0, H - 28*mm, W, 28*mm, fill=1, stroke=0)
        # Logo
        canvas.setFillColor(CREAM)
        canvas.setFont("Helvetica-Bold", 13)
        canvas.drawString(20*mm, H - 16*mm, "Code")
        canvas.setFillColor(ORANGE)
        canvas.drawString(20*mm + canvas.stringWidth("Code", "Helvetica-Bold", 13),
                          H - 16*mm, "Round")
        # Candidate name
        canvas.setFillColor(colors.HexColor("#A8A39C"))
        canvas.setFont("Helvetica", 9)
        canvas.drawRightString(W - 20*mm, H - 16*mm, f"Candidate: {candidate_name}")
        # Footer
        canvas.setFillColor(BORDER)
        canvas.rect(0, 0, W, 12*mm, fill=1, stroke=0)
        canvas.setFillColor(GREY)
        canvas.setFont("Helvetica", 8)
        canvas.drawString(20*mm, 4.5*mm, f"Generated: {generated_at}  ·  CodeRound Interview Platform")
        canvas.drawRightString(W - 20*mm, 4.5*mm, f"Page {doc.page}")
        canvas.restoreState()
    return on_page


# ── Stats table ───────────────────────────────────────────────────────────────
def _stat_table(stats: dict) -> Table:
    """Renders a row of metric tiles."""
    cells = []
    for label, value, color in stats:
        cells.append([
            Paragraph(str(value), _style(fontSize=20, fontName="Helvetica-Bold",
                                          textColor=color, leading=24, alignment=TA_CENTER)),
            Paragraph(label, _style(fontSize=8, fontName="Helvetica", textColor=GREY,
                                     leading=11, alignment=TA_CENTER)),
        ])
    n = len(cells)
    col_w = (W - 40*mm) / n

    data = [[c[0] for c in cells], [c[1] for c in cells]]
    t = Table(data, colWidths=[col_w] * n, rowHeights=[26, 14])
    t.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, -1), CARD_BG),
        ("LINEBELOW",     (0, 0), (-1, 0),  0.5, BORDER),
        ("LINEAFTER",     (0, 0), (-1, -1), 0.5, BORDER),
        ("LINEBEFORE",    (0, 0), (0, -1),  0.5, BORDER),
        ("LINEABOVE",     (0, 0), (-1, 0),  0.5, BORDER),
        ("LINEBELOW",     (0, -1), (-1, -1), 0.5, BORDER),
        ("TOPPADDING",    (0, 0), (-1, 0),  8),
        ("BOTTOMPADDING", (0, -1), (-1, -1), 8),
        ("ALIGN",         (0, 0), (-1, -1), "CENTER"),
        ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
        ("ROUNDEDCORNERS", [4]),
    ]))
    return t


# ── Question block ────────────────────────────────────────────────────────────
def _question_block(idx: int, sub: dict, detail: dict) -> list:
    """Returns a list of flowables for one question + solution."""
    story = []

    title    = sub.get("title", "Untitled")
    category = sub.get("category", "")
    diff     = sub.get("difficulty", "")
    correct  = sub.get("best_correct", False)
    attempts = sub.get("attempts", 0)
    code     = sub.get("last_code", "")
    last_ts  = sub.get("last_attempt", "")

    # ── Question header card ──────────────────────────────────────────────────
    result_bg    = LIGHT_GREEN if correct else LIGHT_RED
    result_color = GREEN       if correct else RED
    result_text  = "✓  Correct" if correct else "✗  Incorrect"

    # Header row: number + title + tags + result badge
    hdr_data = [[
        Paragraph(f"Q{idx}", _style(fontSize=12, fontName="Helvetica-Bold",
                                     textColor=ORANGE, leading=15, alignment=TA_CENTER)),
        Paragraph(f"<b>{title}</b>", _style(fontSize=10.5, fontName="Helvetica-Bold",
                                             textColor=DARK, leading=14)),
        Table([[
            Paragraph(category, _style(fontSize=7.5, fontName="Helvetica-Bold",
                                        textColor=_cat_color(category), leading=10)),
            Paragraph(diff,     _style(fontSize=7.5, fontName="Helvetica-Bold",
                                        textColor=_diff_color(diff), leading=10)),
            Paragraph(f"{attempts} attempt{'s' if attempts != 1 else ''}",
                      _style(fontSize=7.5, fontName="Helvetica", textColor=GREY, leading=10)),
        ]], colWidths=[18*mm, 16*mm, 22*mm],
            style=TableStyle([
                ("ALIGN",   (0,0),(-1,-1), "CENTER"),
                ("VALIGN",  (0,0),(-1,-1), "MIDDLE"),
                ("TOPPADDING",    (0,0),(-1,-1), 2),
                ("BOTTOMPADDING", (0,0),(-1,-1), 2),
            ])),
        Paragraph(result_text, _style(fontSize=9, fontName="Helvetica-Bold",
                                       textColor=result_color, leading=12,
                                       alignment=TA_CENTER)),
    ]]

    hdr = Table(hdr_data, colWidths=[12*mm, 80*mm, 62*mm, 28*mm],
                rowHeights=[20])
    hdr.setStyle(TableStyle([
        ("BACKGROUND",    (0,0),(-1,-1), CARD_BG),
        ("BACKGROUND",    (3,0),(3,0),   result_bg),
        ("LINEABOVE",     (0,0),(-1,0),  1, BORDER),
        ("LINEBELOW",     (0,0),(-1,0),  1, BORDER),
        ("LINEBEFORE",    (0,0),(0,-1),  3, ORANGE),
        ("LINEAFTER",     (-1,0),(-1,-1), 0.5, BORDER),
        ("ALIGN",         (0,0),(0,-1),  "CENTER"),
        ("VALIGN",        (0,0),(-1,-1), "MIDDLE"),
        ("TOPPADDING",    (0,0),(-1,-1), 5),
        ("BOTTOMPADDING", (0,0),(-1,-1), 5),
        ("LEFTPADDING",   (1,0),(1,0),   6),
    ]))
    story.append(hdr)

    # ── Code solution ─────────────────────────────────────────────────────────
    if code and code.strip():
        story.append(Spacer(1, 4))
        story.append(Paragraph("SOLUTION", H2_STYLE))

        # Split code into lines, wrap long lines
        code_lines = code.replace("\t", "    ").split("\n")
        MAX_CHARS = 90
        wrapped = []
        for line in code_lines:
            while len(line) > MAX_CHARS:
                wrapped.append(line[:MAX_CHARS])
                line = "    " + line[MAX_CHARS:]
            wrapped.append(line)

        code_text = "\n".join(wrapped)
        # Escape XML special chars for ReportLab Paragraph
        safe_code = (code_text
                     .replace("&", "&amp;")
                     .replace("<", "&lt;")
                     .replace(">", "&gt;"))
        # Use a Table for the code block (gives us background + border)
        code_para = Paragraph(
            safe_code.replace("\n", "<br/>").replace(" ", "&nbsp;"),
            CODE_STYLE
        )
        code_table = Table([[code_para]],
                           colWidths=[W - 40*mm])
        code_table.setStyle(TableStyle([
            ("BACKGROUND",    (0,0),(-1,-1), DARK),
            ("LINEABOVE",     (0,0),(-1,0),  0.5, colors.HexColor("#3D3A35")),
            ("LINEBELOW",     (0,-1),(-1,-1), 0.5, colors.HexColor("#3D3A35")),
            ("LINEBEFORE",    (0,0),(0,-1),  3, ORANGE),
            ("LINEAFTER",     (-1,0),(-1,-1), 0.5, colors.HexColor("#3D3A35")),
            ("TOPPADDING",    (0,0),(-1,-1), 8),
            ("BOTTOMPADDING", (0,0),(-1,-1), 8),
            ("LEFTPADDING",   (0,0),(-1,-1), 10),
            ("RIGHTPADDING",  (0,0),(-1,-1), 8),
        ]))
        story.append(code_table)

        if last_ts:
            story.append(Paragraph(f"Last submitted: {last_ts}", SMALL_STYLE))
    else:
        story.append(Spacer(1, 4))
        story.append(Paragraph("No solution submitted for this question.", SMALL_STYLE))

    story.append(Spacer(1, 8))
    return story


# ── Main report function ──────────────────────────────────────────────────────
def generate_candidate_report(candidate: dict, detail: dict) -> bytes:
    """
    Generate a PDF report for a candidate.

    Args:
        candidate: dict with keys: id, username, created_at, status
        detail:    dict from db.get_candidate_detail_full()

    Returns:
        PDF bytes
    """
    buf = io.BytesIO()
    generated_at = datetime.now().strftime("%d %b %Y, %H:%M")

    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        leftMargin=20*mm, rightMargin=20*mm,
        topMargin=35*mm,  bottomMargin=20*mm,
        title=f"Interview Report — {candidate['username']}",
        author="CodeRound Platform",
    )

    on_page = _make_page_fn(candidate["username"], generated_at)
    story   = []

    # ── Cover section ─────────────────────────────────────────────────────────
    story.append(Spacer(1, 8*mm))

    # Candidate info card
    status     = candidate.get("status", "active").upper()
    status_clr = GREEN if status == "ACTIVE" else RED
    created    = candidate.get("created_at", "")[:10]
    session_ts = (detail.get("session_started") or "")[:16].replace("T", "  ")

    info_data = [
        [Paragraph("CANDIDATE", LABEL_STYLE),
         Paragraph("INTERVIEW DATE", LABEL_STYLE),
         Paragraph("STATUS", LABEL_STYLE),
         Paragraph("REPORT GENERATED", LABEL_STYLE)],
        [Paragraph(f"<b>{candidate['username']}</b>",
                   _style(fontSize=13, fontName="Helvetica-Bold", textColor=DARK, leading=16)),
         Paragraph(session_ts or created,
                   _style(fontSize=11, fontName="Helvetica", textColor=DARK, leading=14)),
         Paragraph(f"<b>{status}</b>",
                   _style(fontSize=11, fontName="Helvetica-Bold", textColor=status_clr, leading=14)),
         Paragraph(generated_at,
                   _style(fontSize=11, fontName="Helvetica", textColor=DARK, leading=14))],
    ]
    col_w = (W - 40*mm) / 4
    info_t = Table(info_data, colWidths=[col_w]*4, rowHeights=[14, 22])
    info_t.setStyle(TableStyle([
        ("BACKGROUND",    (0,0),(-1,-1), CARD_BG),
        ("LINEABOVE",     (0,0),(-1,0),  0.5, BORDER),
        ("LINEBELOW",     (0,-1),(-1,-1), 0.5, BORDER),
        ("LINEBEFORE",    (0,0),(0,-1),  3, ORANGE),
        ("LINEAFTER",     (-1,0),(-1,-1), 0.5, BORDER),
        ("LINEBELOW",     (0,0),(-1,0),  0.3, BORDER),
        ("TOPPADDING",    (0,0),(-1,0),  6),
        ("BOTTOMPADDING", (0,-1),(-1,-1), 8),
        ("TOPPADDING",    (0,-1),(-1,-1), 6),
        ("LEFTPADDING",   (0,0),(-1,-1), 10),
    ]))
    story.append(info_t)
    story.append(Spacer(1, 6*mm))

    # ── Summary stats ─────────────────────────────────────────────────────────
    story.append(Paragraph("PERFORMANCE SUMMARY", H2_STYLE))
    story.append(OrangeLine())
    story.append(Spacer(1, 3*mm))

    attempted  = detail.get("attempted_count", 0)
    correct    = detail.get("correct_count", 0)
    assigned   = detail.get("assigned_count", 0)
    not_tried  = max(assigned - attempted, 0)
    accuracy   = f"{correct/attempted*100:.0f}%" if attempted else "—"

    stats = [
        ("Assigned",     assigned,  DARK),
        ("Attempted",    attempted, ORANGE),
        ("Correct",      correct,   GREEN),
        ("Incorrect",    attempted - correct, RED),
        ("Not Attempted", not_tried, GREY),
        ("Accuracy",     accuracy,  GREEN if correct > 0 else RED),
    ]
    story.append(_stat_table(stats))
    story.append(Spacer(1, 6*mm))

    # ── Category breakdown ────────────────────────────────────────────────────
    if detail.get("attempted"):
        cats = {}
        for s in detail["attempted"]:
            c = s.get("category", "Other")
            if c not in cats:
                cats[c] = {"total": 0, "correct": 0}
            cats[c]["total"]   += 1
            cats[c]["correct"] += 1 if s.get("best_correct") else 0

        if len(cats) > 1:
            story.append(Paragraph("BREAKDOWN BY CATEGORY", H2_STYLE))
            cat_rows = [
                [Paragraph("Category", LABEL_STYLE),
                 Paragraph("Attempted", LABEL_STYLE),
                 Paragraph("Correct", LABEL_STYLE),
                 Paragraph("Accuracy", LABEL_STYLE)],
            ]
            for cat, v in sorted(cats.items()):
                acc = f"{v['correct']/v['total']*100:.0f}%" if v["total"] else "—"
                cat_rows.append([
                    Paragraph(cat, _style(fontSize=9.5, fontName="Helvetica-Bold",
                                          textColor=_cat_color(cat))),
                    Paragraph(str(v["total"]),   BODY_STYLE),
                    Paragraph(str(v["correct"]), BODY_STYLE),
                    Paragraph(acc,               BODY_STYLE),
                ])
            cat_t = Table(cat_rows, colWidths=[(W-40*mm)*f for f in [.35,.22,.22,.21]])
            cat_t.setStyle(TableStyle([
                ("BACKGROUND",    (0,0), (-1,0),  DARK),
                ("TEXTCOLOR",     (0,0), (-1,0),  CREAM),
                ("ROWBACKGROUNDS",(0,1), (-1,-1), [CARD_BG, CREAM]),
                ("LINEBELOW",     (0,0), (-1,-1), 0.3, BORDER),
                ("TOPPADDING",    (0,0), (-1,-1), 5),
                ("BOTTOMPADDING", (0,0), (-1,-1), 5),
                ("LEFTPADDING",   (0,0), (-1,-1), 8),
            ]))
            story.append(cat_t)
            story.append(Spacer(1, 6*mm))

    # ── Attempted questions with solutions ────────────────────────────────────
    if detail.get("attempted"):
        story.append(Paragraph("ATTEMPTED QUESTIONS & SOLUTIONS", H2_STYLE))
        story.append(OrangeLine())
        story.append(Spacer(1, 3*mm))

        for i, sub in enumerate(detail["attempted"], 1):
            block = _question_block(i, sub, detail)
            story.append(KeepTogether(block[:3]))  # header + label always together
            for fl in block[3:]:
                story.append(fl)

    # ── Not-attempted questions ───────────────────────────────────────────────
    if detail.get("not_attempted"):
        story.append(Spacer(1, 4*mm))
        story.append(Paragraph("NOT ATTEMPTED", H2_STYLE))
        story.append(OrangeLine())
        story.append(Spacer(1, 3*mm))

        na_rows = [[
            Paragraph("Question", LABEL_STYLE),
            Paragraph("Category", LABEL_STYLE),
            Paragraph("Difficulty", LABEL_STYLE),
        ]]
        for q in detail["not_attempted"]:
            na_rows.append([
                Paragraph(q.get("title",""), BODY_STYLE),
                Paragraph(q.get("category",""),
                          _style(fontSize=9, fontName="Helvetica-Bold",
                                  textColor=_cat_color(q.get("category","")))),
                Paragraph(q.get("difficulty",""),
                          _style(fontSize=9, fontName="Helvetica-Bold",
                                  textColor=_diff_color(q.get("difficulty","")))),
            ])
        na_t = Table(na_rows, colWidths=[(W-40*mm)*f for f in [.6, .22, .18]])
        na_t.setStyle(TableStyle([
            ("BACKGROUND",     (0,0),(-1,0),  DARK),
            ("TEXTCOLOR",      (0,0),(-1,0),  CREAM),
            ("ROWBACKGROUNDS", (0,1),(-1,-1), [CARD_BG, CREAM]),
            ("LINEBELOW",      (0,0),(-1,-1), 0.3, BORDER),
            ("TOPPADDING",     (0,0),(-1,-1), 5),
            ("BOTTOMPADDING",  (0,0),(-1,-1), 5),
            ("LEFTPADDING",    (0,0),(-1,-1), 8),
        ]))
        story.append(na_t)

    # Build
    doc.build(story, onFirstPage=on_page, onLaterPages=on_page)
    return buf.getvalue()