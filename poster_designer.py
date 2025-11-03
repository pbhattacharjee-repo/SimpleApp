# poster_designer.py
import json, os
from dataclasses import dataclass, field
from typing import List, Optional, Tuple
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
from reportlab.lib.utils import ImageReader
from reportlab.lib import colors

@dataclass
class Section:
    title: str
    body: str
    bullets: Optional[List[str]] = field(default_factory=list)
    images: Optional[List[dict]] = field(default_factory=list)  # [{"path": "...", "caption": "..."}]

@dataclass
class Layout:
    columns: int = 3
    margins_mm: float = 25.0
    gutter_mm: float = 16.0
    titleband_mm: float = 120.0
    section_title_size: int = 44
    body_size: int = 28
    bullet_indent_mm: float = 8.0

@dataclass
class PosterContent:
    page_mm: Tuple[float, float]
    title: str
    subtitle: Optional[str]
    authors: str
    affiliations: Optional[str]
    logos: Optional[List[str]] = field(default_factory=list)
    theme: Optional[str] = "light"   # "light" or "dark"
    layout: Layout = field(default_factory=Layout)
    sections: List[Section] = field(default_factory=list)
    footer: Optional[str] = None

def _draw_title_band(c, content, W, H, L):
    bg = colors.whitesmoke if content.theme == "light" else colors.darkgray
    fg = colors.black if content.theme == "light" else colors.whitesmoke
    c.setFillColor(bg); c.setStrokeColor(bg)
    c.rect(0, H - L.titleband_mm * mm, W, L.titleband_mm * mm, fill=1, stroke=0)

    # Title (auto shrink)
    c.setFillColor(fg)
    font_size = 72
    max_title_width = W - 2 * L.margins_mm * mm
    while c.stringWidth(content.title, "Helvetica-Bold", font_size) > max_title_width and font_size > 36:
        font_size -= 2
    c.setFont("Helvetica-Bold", font_size)
    c.drawString(L.margins_mm * mm, H - (L.titleband_mm - 30) * mm, content.title)

    # Subtitle
    if content.subtitle:
        c.setFont("Helvetica", 32)
        c.drawString(L.margins_mm * mm, H - (L.titleband_mm - 55) * mm, content.subtitle)

    # Authors and affiliations
    c.setFont("Helvetica", 26)
    authors_y = H - (L.titleband_mm - 85) * mm
    c.drawString(L.margins_mm * mm, authors_y, content.authors)
    if content.affiliations:
        c.setFont("Helvetica-Oblique", 24)
        c.drawString(L.margins_mm * mm, authors_y - 14, content.affiliations)

    # Logos on the right
    x = W - L.margins_mm * mm
    y = H - (L.titleband_mm - 20) * mm
    for logo_path in (content.logos or []):
        try:
            img = ImageReader(logo_path)
            iw, ih = img.getSize()
            scale = min(70 / ih, 2000 / iw)
            draw_w, draw_h = iw * scale, ih * scale
            x_cursor = x - draw_w
            c.drawImage(img, x_cursor, y - draw_h, width=draw_w, height=draw_h, mask='auto')
            x = x_cursor - 10
        except Exception:
            continue

def _split_text_to_lines(c, text, font_name, font_size, max_width):
    c.setFont(font_name, font_size)
    paragraphs = [p.strip() for p in text.split("\n")]
    lines = []
    for p in paragraphs:
        if not p:
            lines.append("")
            continue
        words = p.split()
        cur = []
        for w in words:
            test = " ".join(cur + [w])
            if c.stringWidth(test, font_name, font_size) <= max_width:
                cur.append(w)
            else:
                lines.append(" ".join(cur))
                cur = [w]
        if cur:
            lines.append(" ".join(cur))
    return lines

def _draw_section(c, sec, area_x, area_y, area_w, start_y, L):
    y = start_y

    # Section title
    c.setFont("Helvetica-Bold", L.section_title_size)
    c.setFillColor(colors.black)
    c.drawString(area_x, y, sec.title)
    y -= (L.section_title_size + 8)

    # Body
    body_lines = _split_text_to_lines(c, sec.body, "Helvetica", L.body_size, area_w)
    c.setFont("Helvetica", L.body_size)
    line_height = L.body_size * 1.25
    for line in body_lines:
        if y < area_y:
            return y
        if line == "":
            y -= line_height * 0.6
        else:
            c.drawString(area_x, y, line)
            y -= line_height

    # Bullets
    if sec.bullets:
        bullet_indent = L.bullet_indent_mm * mm
        c.setFont("Helvetica", L.body_size)
        for b in sec.bullets:
            if y < area_y:
                return y
            c.drawString(area_x, y, u"•")
            wrapped = _split_text_to_lines(c, b, "Helvetica", L.body_size, area_w - bullet_indent)
            c.drawString(area_x + bullet_indent, y, wrapped[0])
            y -= line_height
            for wline in wrapped[1:]:
                if y < area_y:
                    return y
                c.drawString(area_x + bullet_indent, y, wline)
                y -= line_height

    # Images
    for img_spec in (sec.images or []):
        if y < area_y:
            return y
        path = img_spec.get("path")
        caption = img_spec.get("caption", "")
        if not path or not os.path.exists(path):
            continue
        try:
            img = ImageReader(path)
            iw, ih = img.getSize()
            max_w = area_w
            scale = min(max_w / iw, 4000 / ih)
            draw_w, draw_h = iw * scale, ih * scale
            if y - draw_h - 24 < area_y:
                return y
            c.drawImage(img, area_x, y - draw_h, width=draw_w, height=draw_h, mask='auto')
            y -= draw_h + 6
            if caption:
                c.setFont("Helvetica-Oblique", max(16, int(L.body_size * 0.7)))
                c.drawString(area_x, y, caption)
                y -= 18
        except Exception:
            continue

    return y

def build_poster(content_json_path: str, out_pdf_path: str):
    with open(content_json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    L = Layout(**data.get("layout", {}))
    sections = [Section(**s) for s in data.get("sections", [])]

    content = PosterContent(
        page_mm=tuple(data.get("page_mm", [1800, 1200])),
        title=data["title"],
        subtitle=data.get("subtitle"),
        authors=data.get("authors", ""),
        affiliations=data.get("affiliations"),
        logos=data.get("logos", []),
        theme=data.get("theme", "light"),
        layout=L,
        sections=sections,
        footer=data.get("footer"),
    )

    W = content.page_mm[0] * mm
    H = content.page_mm[1] * mm

    c = canvas.Canvas(out_pdf_path, pagesize=(W, H))
    # Background
    c.setFillColor(colors.white if content.theme == "light" else colors.black)
    c.rect(0, 0, W, H, fill=1, stroke=0)

    # Title band
    _draw_title_band(c, content, W, H, L)

    # Layout geometry
    left = L.margins_mm * mm
    right = W - L.margins_mm * mm
    bottom = L.margins_mm * mm
    top = H - L.titleband_mm * mm - L.margins_mm * mm
    total_width = right - left
    gutter = L.gutter_mm * mm
    col_w = (total_width - (L.columns - 1) * gutter) / L.columns

    # Flow sections column by column
    cur_col = 0
    x = left
    y = top
    area_y = bottom

    for sec in content.sections:
        y_after = _draw_section(c, sec, x, area_y, col_w, y, L)
        if y_after < area_y + 60:
            cur_col += 1
            if cur_col >= L.columns:
                # New page if we run out of columns
                c.showPage()
                c.setFillColor(colors.white if content.theme == "light" else colors.black)
                c.rect(0, 0, W, H, fill=1, stroke=0)
                _draw_title_band(c, content, W, H, L)
                cur_col = 0
            x = left + cur_col * (col_w + gutter)
            y = top
            y_after = _draw_section(c, sec, x, area_y, col_w, y, L)
        y = y_after - 18  # spacing after each section

    # Footer
    if content.footer:
        c.setFont("Helvetica", 20)
        c.setFillColor(colors.black)
        c.drawRightString(right, bottom - 10, content.footer)

    c.save()
