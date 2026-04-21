#!/usr/bin/env python3
"""
Data-driven PDF report generator — professional business-report style.
Uses ReportLab Platypus for high-quality CJK/Latin mixed text layout.

Reads a JSON specification and outputs a professionally styled PDF with:
  - Cover page with metadata table and disclaimer
  - Auto-generated Table of Contents with page numbers
  - Numbered section headings (1. / 2.1 / 2.2 ...)
  - Dense, detailed content with proper typography
  - Tables with auto column widths, text wrapping, left-aligned text columns
  - References / footnotes section
  - Page headers and footers

Usage:
    python3 generate_report.py <data.json> [output.pdf]

JSON schema — see SKILL.md for full documentation.
"""

from __future__ import annotations

import sys
import os
import json
import re
import subprocess
import tempfile

# ---------------------------------------------------------------------------
# Ensure reportlab is available
# ---------------------------------------------------------------------------

def _ensure_reportlab():
    try:
        import reportlab  # noqa: F401
    except ImportError:
        subprocess.check_call(
            [sys.executable, "-m", "pip", "install", "reportlab", "-q"],
            stdout=subprocess.DEVNULL,
        )

_ensure_reportlab()

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT, TA_JUSTIFY
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm, cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from reportlab.platypus import (
    BaseDocTemplate,
    Frame,
    Image,
    KeepTogether,
    NextPageTemplate,
    PageBreak,
    PageTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)
from reportlab.platypus.tableofcontents import TableOfContents

# ---------------------------------------------------------------------------
# Color palette (matches original design)
# ---------------------------------------------------------------------------

NAVY = colors.Color(26 / 255, 54 / 255, 93 / 255)
ACCENT = colors.Color(43 / 255, 108 / 255, 176 / 255)
BRIGHT = colors.Color(49 / 255, 130 / 255, 206 / 255)
LIGHT_BG = colors.Color(237 / 255, 242 / 255, 247 / 255)
TEXT_DARK = colors.Color(33 / 255, 37 / 255, 41 / 255)
TEXT_BODY = colors.Color(55 / 255, 65 / 255, 81 / 255)
TEXT_MUTED = colors.Color(113 / 255, 128 / 255, 150 / 255)
DIVIDER = colors.Color(203 / 255, 213 / 255, 224 / 255)
TBL_HDR_BG = NAVY
TBL_ALT_BG = colors.Color(245 / 255, 247 / 255, 250 / 255)
TBL_BORDER = colors.Color(220 / 255, 225 / 255, 230 / 255)
CALLOUT_BG = colors.Color(239 / 255, 246 / 255, 255 / 255)
CALLOUT_BAR = BRIGHT
REF_COLOR = colors.Color(80 / 255, 80 / 255, 80 / 255)

PAGE_W, PAGE_H = A4  # 210mm x 297mm
MARGIN_L = 25 * mm
MARGIN_R = 20 * mm
MARGIN_T = 22 * mm
MARGIN_B = 20 * mm
CONTENT_W = PAGE_W - MARGIN_L - MARGIN_R  # ~165mm

# ---------------------------------------------------------------------------
# CJK font registration
# ---------------------------------------------------------------------------

def _has_cjk(text: str) -> bool:
    for ch in text:
        cp = ord(ch)
        if (0x4E00 <= cp <= 0x9FFF or 0x3400 <= cp <= 0x4DBF
                or 0x3000 <= cp <= 0x303F or 0xFF00 <= cp <= 0xFFEF
                or 0xAC00 <= cp <= 0xD7AF):
            return True
    return False


_CJK_REGISTERED = False
_FONT_BODY = "Helvetica"
_FONT_BOLD = "Helvetica-Bold"
_FONT_ITALIC = "Helvetica-Oblique"
_FONT_SERIF = "Times-Roman"
_FONT_SERIF_BOLD = "Times-Bold"

_TTF_CJK_CANDIDATES = [
    ("/usr/share/fonts/truetype/wqy/wqy-microhei.ttc", 0),
    ("/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc", 0),
    ("/usr/share/fonts/wqy-microhei/wqy-microhei.ttc", 0),
    ("/usr/share/fonts/truetype/noto/NotoSansCJKsc-Regular.ttf", None),
]


def _register_cjk_fonts():
    """Register CJK fonts — prefer TTF (sandbox), fallback to CID STSong-Light."""
    global _CJK_REGISTERED, _FONT_BODY, _FONT_BOLD, _FONT_ITALIC
    global _FONT_SERIF, _FONT_SERIF_BOLD
    if _CJK_REGISTERED:
        return

    from reportlab.pdfbase.ttfonts import TTFont

    # Strategy 1: TTF fonts (Linux sandbox — WenQuanYi Micro Hei)
    for path, subfont_idx in _TTF_CJK_CANDIDATES:
        if not os.path.exists(path):
            continue
        try:
            kw = {"subfontIndex": subfont_idx} if subfont_idx is not None else {}
            pdfmetrics.registerFont(TTFont("CJK", path, **kw))
            pdfmetrics.registerFont(TTFont("CJK-Bold", path, **kw))
            _FONT_BODY = "CJK"
            _FONT_BOLD = "CJK-Bold"
            _FONT_ITALIC = "CJK"
            _FONT_SERIF = "CJK"
            _FONT_SERIF_BOLD = "CJK-Bold"
            _CJK_REGISTERED = True
            print(f"Registered CJK TTF font: {path}")
            return
        except Exception:
            continue

    # Strategy 2: CID font STSong-Light (works everywhere reportlab is installed)
    try:
        pdfmetrics.registerFont(UnicodeCIDFont("STSong-Light"))
        _FONT_BODY = "STSong-Light"
        _FONT_BOLD = "STSong-Light"
        _FONT_ITALIC = "STSong-Light"
        _FONT_SERIF = "STSong-Light"
        _FONT_SERIF_BOLD = "STSong-Light"
        _CJK_REGISTERED = True
        print("Registered CJK CID font: STSong-Light")
    except Exception as e:
        print(f"WARNING: Failed to register CJK fonts: {e}", file=sys.stderr)


# ---------------------------------------------------------------------------
# Paragraph styles
# ---------------------------------------------------------------------------

def _build_styles() -> dict[str, ParagraphStyle]:
    """Build all paragraph styles used in the report."""
    ww = "CJK" if _CJK_REGISTERED else None
    s: dict[str, ParagraphStyle] = {}

    s["body"] = ParagraphStyle(
        "body", fontName=_FONT_SERIF, fontSize=10, leading=15,
        textColor=TEXT_BODY, alignment=TA_LEFT, wordWrap=ww,
        spaceBefore=2, spaceAfter=4,
    )
    s["body_justify"] = ParagraphStyle(
        "body_justify", parent=s["body"], alignment=TA_JUSTIFY,
    )
    s["h1"] = ParagraphStyle(
        "h1", fontName=_FONT_BOLD, fontSize=16, leading=20,
        textColor=NAVY, alignment=TA_LEFT, wordWrap=ww,
        spaceBefore=6, spaceAfter=4,
    )
    s["h2"] = ParagraphStyle(
        "h2", fontName=_FONT_BOLD, fontSize=14, leading=18,
        textColor=NAVY, alignment=TA_LEFT, wordWrap=ww,
        spaceBefore=8, spaceAfter=4,
    )
    s["h3"] = ParagraphStyle(
        "h3", fontName=_FONT_BOLD, fontSize=10, leading=15,
        textColor=ACCENT, alignment=TA_LEFT, wordWrap=ww,
        spaceBefore=6, spaceAfter=3,
    )
    s["sub_heading"] = ParagraphStyle(
        "sub_heading", fontName=_FONT_BOLD, fontSize=11, leading=14,
        textColor=NAVY, alignment=TA_LEFT, wordWrap=ww,
        spaceBefore=4, spaceAfter=2,
    )
    s["bullet"] = ParagraphStyle(
        "bullet", fontName=_FONT_SERIF, fontSize=10, leading=14,
        textColor=TEXT_BODY, alignment=TA_LEFT, wordWrap=ww,
        leftIndent=8 * mm, bulletIndent=3 * mm,
        spaceBefore=1, spaceAfter=2,
    )
    s["ref"] = ParagraphStyle(
        "ref", fontName=_FONT_BODY, fontSize=8.5, leading=12,
        textColor=REF_COLOR, alignment=TA_LEFT, wordWrap=ww,
        leftIndent=10 * mm,
        spaceBefore=1, spaceAfter=6,
    )
    s["ref_label"] = ParagraphStyle(
        "ref_label", fontName=_FONT_BOLD, fontSize=8.5, leading=12,
        textColor=NAVY, alignment=TA_LEFT,
    )
    s["table_header"] = ParagraphStyle(
        "table_header", fontName=_FONT_BOLD, fontSize=9, leading=12,
        textColor=colors.white, alignment=TA_CENTER, wordWrap=ww,
    )
    s["table_cell"] = ParagraphStyle(
        "table_cell", fontName=_FONT_SERIF, fontSize=9, leading=12,
        textColor=TEXT_BODY, alignment=TA_LEFT, wordWrap=ww,
    )
    s["table_cell_center"] = ParagraphStyle(
        "table_cell_center", parent=s["table_cell"], alignment=TA_CENTER,
    )
    s["kv_key"] = ParagraphStyle(
        "kv_key", fontName=_FONT_BOLD, fontSize=9.5, leading=13,
        textColor=NAVY, alignment=TA_LEFT, wordWrap=ww,
    )
    s["kv_val"] = ParagraphStyle(
        "kv_val", fontName=_FONT_SERIF, fontSize=9.5, leading=13,
        textColor=TEXT_BODY, alignment=TA_LEFT, wordWrap=ww,
    )
    s["callout_title"] = ParagraphStyle(
        "callout_title", fontName=_FONT_BOLD, fontSize=10, leading=14,
        textColor=NAVY, alignment=TA_LEFT, wordWrap=ww,
    )
    s["callout_body"] = ParagraphStyle(
        "callout_body", fontName=_FONT_SERIF, fontSize=9.5, leading=13,
        textColor=TEXT_BODY, alignment=TA_LEFT, wordWrap=ww,
    )
    s["caption"] = ParagraphStyle(
        "caption", fontName=_FONT_ITALIC, fontSize=8.5, leading=11,
        textColor=TEXT_MUTED, alignment=TA_LEFT, wordWrap=ww,
    )
    s["cover_title"] = ParagraphStyle(
        "cover_title", fontName=_FONT_BOLD, fontSize=26, leading=32,
        textColor=NAVY, alignment=TA_LEFT, wordWrap=ww,
    )
    s["cover_subtitle"] = ParagraphStyle(
        "cover_subtitle", fontName=_FONT_BODY, fontSize=14, leading=18,
        textColor=ACCENT, alignment=TA_LEFT, wordWrap=ww,
    )
    s["cover_disclaimer"] = ParagraphStyle(
        "cover_disclaimer", fontName=_FONT_ITALIC, fontSize=8, leading=11,
        textColor=TEXT_MUTED, alignment=TA_LEFT, wordWrap=ww,
    )

    # TOC styles
    s["toc_h1"] = ParagraphStyle(
        "toc_h1", fontName=_FONT_BOLD, fontSize=11, leading=16,
        textColor=NAVY, leftIndent=0,
    )
    s["toc_h2"] = ParagraphStyle(
        "toc_h2", fontName=_FONT_BODY, fontSize=10, leading=14,
        textColor=TEXT_BODY, leftIndent=10 * mm,
    )
    s["toc_h3"] = ParagraphStyle(
        "toc_h3", fontName=_FONT_BODY, fontSize=9.5, leading=13,
        textColor=TEXT_MUTED, leftIndent=20 * mm,
    )

    return s


# ---------------------------------------------------------------------------
# Custom flowables
# ---------------------------------------------------------------------------

from reportlab.platypus import Flowable


class AccentLine(Flowable):
    """A short colored accent line."""

    def __init__(self, width=40 * mm, thickness=0.8, color=ACCENT):
        super().__init__()
        self.line_width = width
        self.thickness = thickness
        self.color = color
        self.height = self.thickness + 2

    def wrap(self, availWidth, availHeight):
        return (self.line_width, self.height)

    def draw(self):
        self.canv.setStrokeColor(self.color)
        self.canv.setLineWidth(self.thickness)
        self.canv.line(0, 1, self.line_width, 1)


class DividerLine(Flowable):
    """A full-width divider line."""

    def __init__(self, color=DIVIDER, thickness=0.3):
        super().__init__()
        self.color = color
        self.thickness = thickness
        self.height = self.thickness + 6

    def wrap(self, availWidth, availHeight):
        self._avail_w = availWidth
        return (availWidth, self.height)

    def draw(self):
        self.canv.setStrokeColor(self.color)
        self.canv.setLineWidth(self.thickness)
        self.canv.line(0, 3, self._avail_w, 3)


class LeftBarParagraph(Flowable):
    """A paragraph with a colored left bar (for H1 headings).

    Propagates _toc_entry from the inner paragraph so afterFlowable can see it.
    """

    def __init__(self, paragraph: Paragraph, bar_color=ACCENT, bar_width=2):
        super().__init__()
        self.paragraph = paragraph
        self.bar_color = bar_color
        self.bar_width = bar_width
        if hasattr(paragraph, "_toc_entry"):
            self._toc_entry = paragraph._toc_entry

    def wrap(self, availWidth, availHeight):
        w, h = self.paragraph.wrap(availWidth - self.bar_width - 3, availHeight)
        self.para_w = w
        self.para_h = h
        return (availWidth, h)

    def draw(self):
        self.canv.setFillColor(self.bar_color)
        self.canv.rect(-2, 0, self.bar_width, self.para_h, fill=1, stroke=0)
        self.paragraph.drawOn(self.canv, self.bar_width + 3, 0)


class CalloutBox(Flowable):
    """A callout box with background color and left accent bar."""

    def __init__(self, content_flowables: list, bg_color=CALLOUT_BG,
                 bar_color=CALLOUT_BAR, bar_width=2.5, padding=8):
        super().__init__()
        self.content = content_flowables
        self.bg_color = bg_color
        self.bar_color = bar_color
        self.bar_width = bar_width
        self.padding = padding

    def wrap(self, availWidth, availHeight):
        self._avail_w = availWidth
        inner_w = availWidth - self.bar_width - self.padding * 2
        total_h = self.padding
        for f in self.content:
            w, h = f.wrap(inner_w, availHeight)
            total_h += h
        total_h += self.padding
        self._total_h = total_h
        return (availWidth, total_h)

    def draw(self):
        self.canv.setFillColor(self.bg_color)
        self.canv.rect(0, 0, self._avail_w, self._total_h, fill=1, stroke=0)
        self.canv.setFillColor(self.bar_color)
        self.canv.rect(0, 0, self.bar_width, self._total_h, fill=1, stroke=0)

        inner_w = self._avail_w - self.bar_width - self.padding * 2
        y = self._total_h - self.padding
        for f in self.content:
            w, h = f.wrap(inner_w, y)
            y -= h
            f.drawOn(self.canv, self.bar_width + self.padding, y)


# ---------------------------------------------------------------------------
# Cover page (drawn via Canvas callback)
# ---------------------------------------------------------------------------

def _draw_cover(canvas, doc):
    """Draw the cover page using low-level Canvas operations."""
    data = doc._report_data
    canvas.saveState()

    # Top navy bar
    canvas.setFillColor(NAVY)
    canvas.rect(0, PAGE_H - 12 * mm, PAGE_W, 12 * mm, fill=1, stroke=0)

    # Title
    y = PAGE_H - 65 * mm
    canvas.setFont(_FONT_BOLD, 26)
    canvas.setFillColor(NAVY)
    title = data.get("title", "Report")
    _draw_wrapped_text(canvas, title, MARGIN_L, y, CONTENT_W, 26, 32)
    title_lines = _count_lines(title, CONTENT_W, _FONT_BOLD, 26)
    y -= title_lines * 32 + 4

    # Subtitle
    subtitle = data.get("subtitle", "")
    if subtitle:
        canvas.setFont(_FONT_BODY, 14)
        canvas.setFillColor(ACCENT)
        _draw_wrapped_text(canvas, subtitle, MARGIN_L, y, CONTENT_W, 14, 18)
        sub_lines = _count_lines(subtitle, CONTENT_W, _FONT_BODY, 14)
        y -= sub_lines * 18 + 4

    # Accent line
    canvas.setStrokeColor(ACCENT)
    canvas.setLineWidth(0.8)
    y -= 4
    canvas.line(MARGIN_L, y, MARGIN_L + 55 * mm, y)
    y -= 14

    # Cover metadata table
    meta = data.get("cover_meta", [])
    if meta:
        key_w = 55 * mm
        val_w = 105 * mm
        rh = 7 * mm
        for i, item in enumerate(meta):
            if len(item) < 2:
                continue
            if i % 2 == 0:
                canvas.setFillColor(LIGHT_BG)
                canvas.rect(MARGIN_L, y - rh, key_w + val_w, rh, fill=1, stroke=0)
            canvas.setFont(_FONT_BOLD, 9.5)
            canvas.setFillColor(NAVY)
            canvas.drawString(MARGIN_L + 2 * mm, y - rh + 2 * mm, str(item[0]))
            canvas.setFont(_FONT_BODY, 9.5)
            canvas.setFillColor(TEXT_BODY)
            canvas.drawString(MARGIN_L + key_w + 2 * mm, y - rh + 2 * mm, str(item[1]))
            y -= rh

    # Disclaimer at bottom
    disclaimer = data.get("disclaimer", "")
    if disclaimer:
        canvas.setFont(_FONT_ITALIC, 8)
        canvas.setFillColor(TEXT_MUTED)
        _draw_wrapped_text(canvas, disclaimer, MARGIN_L, 40 * mm, CONTENT_W, 8, 11)

    # Bottom navy bar
    canvas.setFillColor(NAVY)
    canvas.rect(0, 0, PAGE_W, 10 * mm, fill=1, stroke=0)

    canvas.restoreState()


def _tokenize_for_wrap(text: str) -> list[str]:
    """Split text into tokens suitable for line wrapping.

    Latin words stay together; CJK characters become individual tokens
    so they can break at any character boundary.
    """
    tokens: list[str] = []
    buf = ""
    for ch in text:
        if _has_cjk(ch):
            if buf:
                tokens.append(buf)
                buf = ""
            tokens.append(ch)
        elif ch == " ":
            if buf:
                tokens.append(buf)
                buf = ""
            tokens.append(" ")
        else:
            buf += ch
    if buf:
        tokens.append(buf)
    return tokens


def _draw_wrapped_text(canvas, text: str, x, y, max_width, font_size, leading):
    """Draw text that wraps within max_width, supporting CJK character-level breaks."""
    font_name = canvas._fontname
    tokens = _tokenize_for_wrap(text)
    line = ""
    for token in tokens:
        test = line + token
        if canvas.stringWidth(test.strip(), font_name, font_size) > max_width and line.strip():
            canvas.drawString(x, y, line.strip())
            y -= leading
            line = token if token != " " else ""
        else:
            line = test
    if line.strip():
        canvas.drawString(x, y, line.strip())


def _count_lines(text: str, max_width, font_name, font_size) -> int:
    """Estimate number of wrapped lines for cover layout, supporting CJK."""
    from reportlab.pdfbase.pdfmetrics import stringWidth
    tokens = _tokenize_for_wrap(text)
    lines = 1
    line = ""
    for token in tokens:
        test = line + token
        if stringWidth(test.strip(), font_name, font_size) > max_width and line.strip():
            lines += 1
            line = token if token != " " else ""
        else:
            line = test
    return lines


# ---------------------------------------------------------------------------
# Header / Footer (drawn via Canvas callback)
# ---------------------------------------------------------------------------

def _draw_header_footer(canvas, doc):
    """Draw header and footer on content pages."""
    data = doc._report_data
    canvas.saveState()

    # Header
    title = data.get("short_title", "") or data.get("title", "")
    report_type = data.get("report_type", "")
    canvas.setFont(_FONT_BODY, 8)
    canvas.setFillColor(TEXT_MUTED)
    canvas.drawString(MARGIN_L, PAGE_H - 12 * mm, title[:60])
    canvas.drawRightString(PAGE_W - MARGIN_R, PAGE_H - 12 * mm, report_type[:40])
    canvas.setStrokeColor(DIVIDER)
    canvas.setLineWidth(0.3)
    canvas.line(MARGIN_L, PAGE_H - 14 * mm, PAGE_W - MARGIN_R, PAGE_H - 14 * mm)

    # Footer
    canvas.setStrokeColor(DIVIDER)
    canvas.setLineWidth(0.2)
    canvas.line(MARGIN_L, MARGIN_B - 2 * mm, PAGE_W - MARGIN_R, MARGIN_B - 2 * mm)
    canvas.setFont(_FONT_BODY, 8)
    canvas.setFillColor(TEXT_MUTED)
    page_text = f"-- {canvas.getPageNumber()} --"
    canvas.drawCentredString(PAGE_W / 2, MARGIN_B - 8 * mm, page_text)

    canvas.restoreState()


def _draw_toc_header(canvas, doc):
    """Minimal header for TOC page (no running header)."""
    data = doc._report_data
    canvas.saveState()
    # Footer only
    canvas.setStrokeColor(DIVIDER)
    canvas.setLineWidth(0.2)
    canvas.line(MARGIN_L, MARGIN_B - 2 * mm, PAGE_W - MARGIN_R, MARGIN_B - 2 * mm)
    canvas.setFont(_FONT_BODY, 8)
    canvas.setFillColor(TEXT_MUTED)
    page_text = f"-- {canvas.getPageNumber()} --"
    canvas.drawCentredString(PAGE_W / 2, MARGIN_B - 8 * mm, page_text)
    canvas.restoreState()


# ---------------------------------------------------------------------------
# Document template
# ---------------------------------------------------------------------------

class ReportDocTemplate(BaseDocTemplate):
    """Custom doc template with TOC support via afterFlowable / multiBuild."""

    def __init__(self, filename, report_data, **kwargs):
        self._report_data = report_data
        self._toc = TableOfContents()
        super().__init__(filename, **kwargs)

    def afterFlowable(self, flowable):
        """Capture heading flowables for TOC."""
        if hasattr(flowable, "_toc_entry"):
            level, text = flowable._toc_entry
            key = f"toc_{id(flowable)}"
            self.notify("TOCEntry", (level, text, self.page, key))
            self.canv.bookmarkPage(key)


# ---------------------------------------------------------------------------
# Heading helper — attaches TOC metadata
# ---------------------------------------------------------------------------

class HeadingParagraph(Paragraph):
    """A Paragraph that carries TOC metadata."""

    def __init__(self, text, style, level=0, toc_text="", **kwargs):
        super().__init__(text, style, **kwargs)
        self._toc_entry = (level, toc_text or text)


# ---------------------------------------------------------------------------
# HTML escaping for Paragraph XML
# ---------------------------------------------------------------------------

def _esc(text) -> str:
    """Escape text for ReportLab Paragraph XML."""
    if text is None:
        return ""
    text = str(text)
    text = text.replace("&", "&amp;")
    text = text.replace("<", "&lt;")
    text = text.replace(">", "&gt;")
    return text


def _normalize_body(text: str) -> str:
    """Normalize text body for better rendering.

    - Merge lines where a numbered item (e.g. '1.\\n') is split from its content
    - Collapse single newlines within a paragraph into spaces
    - Preserve double newlines as paragraph separators
    """
    text = re.sub(r'(\d+\.)\s*\n(?!\n)', r'\1 ', text)
    return text


_CITE_RE = re.compile(r'\[(\d+(?:\s*[,，、]\s*\d+)*)\]')

_AVAILABLE_REF_COUNT = 0


def _linkify_citations(escaped_xml: str) -> str:
    """Convert [n] or [1,2,3] citation markers in already-escaped XML
    into superscript links pointing to ref_n anchors.
    Only creates links for citations that have a corresponding reference
    anchor (i.e. n <= _AVAILABLE_REF_COUNT); others render as plain
    superscript text to avoid unresolved destination errors."""
    def _repl(m):
        raw = m.group(1)
        nums = re.split(r'\s*[,，、]\s*', raw)
        parts = []
        for n in nums:
            n = n.strip()
            if n.isdigit() and 1 <= int(n) <= _AVAILABLE_REF_COUNT:
                parts.append(
                    f'<a href="#ref_{n}" color="#{_color_hex(ACCENT)}">[{n}]</a>'
                )
            else:
                parts.append(f'[{n}]')
        return f'<super>{"".join(parts)}</super>'
    return _CITE_RE.sub(_repl, escaped_xml)


# ---------------------------------------------------------------------------
# Section renderers — each returns a list of Flowables
# ---------------------------------------------------------------------------

def _render_heading(sec, styles) -> list:
    level = sec.get("level", 1)
    text = sec.get("text", "")
    number = sec.get("number", "")
    display = f"{number} {text}".strip() if number else text

    result = []
    if level == 1:
        result.append(DividerLine())
        result.append(Spacer(1, 2 * mm))
        para = HeadingParagraph(_esc(display), styles["h1"], level=0, toc_text=display)
        result.append(LeftBarParagraph(para))
        result.append(AccentLine(width=40 * mm))
        result.append(Spacer(1, 3 * mm))
    elif level == 2:
        result.append(Spacer(1, 2 * mm))
        para = HeadingParagraph(_esc(display), styles["h2"], level=1, toc_text=display)
        result.append(para)
        result.append(Spacer(1, 2 * mm))
    else:
        result.append(Spacer(1, 1.5 * mm))
        para = HeadingParagraph(_esc(display), styles["h3"], level=2, toc_text=display)
        result.append(para)
        result.append(Spacer(1, 1.5 * mm))
    return result


def _md_bold(escaped_xml: str) -> str:
    """Convert **bold** markers (in already-escaped XML) to <b> tags."""
    return re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', escaped_xml)


def _render_text(sec, styles) -> list:
    heading = sec.get("heading", "")
    body = sec.get("body", "")
    result = []

    if heading:
        result.append(Paragraph(_esc(heading), styles["sub_heading"]))
        result.append(Spacer(1, 1 * mm))

    if not body:
        return result

    body = _normalize_body(body)

    _RE_MD_HEADING = re.compile(r'^(#{1,4})\s+(.*)')
    _RE_BULLET = re.compile(r'^[-*]\s+(.*)')
    _RE_NUMLIST = re.compile(r'^\d+[.)]\s+(.*)')
    _RE_TABLE_ROW = re.compile(r'^\|(.+)\|$')
    _RE_TABLE_SEP = re.compile(r'^\|[\s:|-]+\|$')

    pending_text: list[str] = []
    pending_table: list[str] = []

    def _flush_paragraph():
        if not pending_text:
            return
        para = ' '.join(pending_text)
        pending_text.clear()
        xml = _md_bold(_linkify_citations(_esc(para)))
        result.append(Paragraph(xml, styles["body_justify"]))

    def _flush_table():
        if not pending_table:
            return
        rows_raw = pending_table[:]
        pending_table.clear()
        parsed = []
        for r in rows_raw:
            if _RE_TABLE_SEP.match(r):
                continue
            cells = [c.strip() for c in r.strip('|').split('|')]
            parsed.append(cells)
        if len(parsed) < 2:
            return
        headers = parsed[0]
        data_rows = parsed[1:]
        tbl_sec = {"headers": headers, "rows": data_rows}
        result.extend(_render_table(tbl_sec, styles))

    for line in body.split('\n'):
        stripped = line.strip()

        if _RE_TABLE_ROW.match(stripped):
            _flush_paragraph()
            pending_table.append(stripped)
            continue
        elif pending_table:
            _flush_table()

        if not stripped:
            _flush_paragraph()
            continue

        hm = _RE_MD_HEADING.match(stripped)
        if hm:
            _flush_paragraph()
            level = len(hm.group(1))
            htext = hm.group(2)
            style_key = "h3" if level >= 3 else "h2" if level == 2 else "sub_heading"
            result.append(Spacer(1, 2 * mm))
            result.append(Paragraph(_md_bold(_esc(htext)), styles[style_key]))
            result.append(Spacer(1, 1 * mm))
            continue

        bm = _RE_BULLET.match(stripped)
        if not bm:
            bm = _RE_NUMLIST.match(stripped)
        if bm:
            _flush_paragraph()
            item_text = bm.group(1)
            xml = _md_bold(_linkify_citations(_esc(item_text)))
            bullet_char = "\u2022"
            bxml = f'<font color="#{_color_hex(ACCENT)}">{bullet_char}</font>&nbsp;&nbsp;{xml}'
            result.append(Paragraph(bxml, styles["bullet"]))
            continue

        pending_text.append(stripped)

    _flush_table()
    _flush_paragraph()
    result.append(Spacer(1, 2 * mm))
    return result


def _render_bullets(sec, styles) -> list:
    heading = sec.get("heading", "")
    items = sec.get("items", [])
    result = []

    if heading:
        result.append(Paragraph(_esc(heading), styles["sub_heading"]))
        result.append(Spacer(1, 1 * mm))

    for item in items:
        bullet_char = "\u2022"
        escaped = _linkify_citations(_esc(str(item)))
        text = f'<font color="#{_color_hex(ACCENT)}">{bullet_char}</font>&nbsp;&nbsp;{escaped}'
        result.append(Paragraph(text, styles["bullet"]))

    result.append(Spacer(1, 2 * mm))
    return result


def _color_hex(c) -> str:
    """Convert a reportlab Color to hex string (without #)."""
    return "%02x%02x%02x" % (int(c.red * 255), int(c.green * 255), int(c.blue * 255))


def _render_table(sec, styles) -> list:
    heading = sec.get("heading", "")
    headers = sec.get("headers", [])
    rows = sec.get("rows", [])
    align_spec = sec.get("align", None)
    caption = sec.get("caption", "")
    result = []

    if heading:
        result.append(Paragraph(_esc(heading), styles["sub_heading"]))
        result.append(Spacer(1, 2 * mm))

    n_cols = len(headers or (rows[0] if rows else []))
    if n_cols == 0:
        return result

    if not align_spec:
        align_spec = _auto_col_align(rows, n_cols)

    col_widths = sec.get("col_widths")
    if col_widths:
        col_widths = [w * mm for w in col_widths]
    else:
        col_widths = _auto_col_widths(headers, rows, n_cols, styles)

    def _cell_style(ci):
        a = align_spec[ci] if ci < len(align_spec) else "L"
        if a == "C":
            return styles["table_cell_center"]
        return styles["table_cell"]

    table_data = []
    if headers:
        hdr_row = [Paragraph(_esc(str(h)), styles["table_header"]) for h in headers]
        table_data.append(hdr_row)

    for row in rows:
        data_row = []
        for ci, val in enumerate(row):
            data_row.append(Paragraph(_esc(str(val)), _cell_style(ci)))
        table_data.append(data_row)

    if not table_data:
        return result

    tbl = Table(table_data, colWidths=col_widths, repeatRows=1 if headers else 0)

    cmds = [
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("LINEBELOW", (0, -1), (-1, -1), 0.5, TBL_BORDER),
    ]

    if headers:
        cmds.extend([
            ("BACKGROUND", (0, 0), (-1, 0), TBL_HDR_BG),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("LINEBELOW", (0, 0), (-1, 0), 1, colors.white),
        ])
        for ri in range(1, len(table_data)):
            if ri % 2 == 0:
                cmds.append(("BACKGROUND", (0, ri), (-1, ri), TBL_ALT_BG))
    else:
        for ri in range(len(table_data)):
            if ri % 2 == 1:
                cmds.append(("BACKGROUND", (0, ri), (-1, ri), TBL_ALT_BG))

    tbl.setStyle(TableStyle(cmds))
    result.append(tbl)

    if caption:
        result.append(Spacer(1, 1 * mm))
        result.append(Paragraph(_esc(caption), styles["caption"]))

    result.append(Spacer(1, 3 * mm))
    return result


def _auto_col_widths(headers, rows, n_cols, styles) -> list[float]:
    """Calculate column widths proportionally based on content."""
    from reportlab.pdfbase.pdfmetrics import stringWidth

    font_name = _FONT_SERIF
    font_size = 9
    avail = CONTENT_W

    max_w = [0.0] * n_cols
    for i, h in enumerate(headers or [""] * n_cols):
        if i < n_cols:
            max_w[i] = max(max_w[i], stringWidth(str(h), _FONT_BOLD, 9) + 10)

    sample = rows[:15]
    for row in sample:
        for ci, val in enumerate(row):
            if ci < n_cols:
                w = stringWidth(str(val), font_name, font_size) + 10
                max_w[ci] = max(max_w[ci], min(w, avail * 0.45))

    total = sum(max_w) or 1
    raw = [w / total * avail for w in max_w]
    col_min = max(avail / n_cols * 0.4, 14 * mm)
    widths = [max(w, col_min) for w in raw]
    wt = sum(widths) or 1
    return [w / wt * avail for w in widths]


def _auto_col_align(rows, n_cols) -> list[str]:
    """Auto-detect column alignment based on content."""
    aligns = ["L"] * n_cols
    sample = rows[:10]
    for ci in range(n_cols):
        numeric_count = 0
        for row in sample:
            if ci < len(row):
                val = str(row[ci]).strip()
                cleaned = re.sub(r'[$%,+\-\s]', '', val)
                if cleaned.replace('.', '', 1).isdigit():
                    numeric_count += 1
        if numeric_count > len(sample) * 0.5:
            aligns[ci] = "C"
    return aligns


def _render_kv(sec, styles) -> list:
    heading = sec.get("heading", "")
    items = sec.get("items", [])
    result = []

    if heading:
        result.append(Paragraph(_esc(heading), styles["sub_heading"]))
        result.append(Spacer(1, 1 * mm))

    key_w_mm = sec.get("key_width", 50)
    key_w = key_w_mm * mm
    val_w = CONTENT_W - key_w

    table_data = []
    for pair in items:
        if len(pair) < 2:
            continue
        table_data.append([
            Paragraph(_esc(str(pair[0])), styles["kv_key"]),
            Paragraph(_esc(str(pair[1])), styles["kv_val"]),
        ])

    if not table_data:
        return result

    tbl = Table(table_data, colWidths=[key_w, val_w])
    cmds = [
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 2),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
        ("LEFTPADDING", (0, 0), (-1, -1), 3),
        ("RIGHTPADDING", (0, 0), (-1, -1), 3),
    ]
    for ri in range(len(table_data)):
        if ri % 2 == 0:
            cmds.append(("BACKGROUND", (0, ri), (-1, ri), LIGHT_BG))
    tbl.setStyle(TableStyle(cmds))
    result.append(tbl)
    result.append(Spacer(1, 3 * mm))
    return result


def _render_image(sec, styles) -> list:
    path = sec.get("path", "")
    caption = sec.get("caption", "")
    width = sec.get("width", 150)
    result = []

    if not path or not os.path.isfile(path):
        return result

    max_w = CONTENT_W
    max_h = PAGE_H - MARGIN_T - MARGIN_B - 30 * mm  # leave room for caption + spacing

    try:
        from reportlab.lib.utils import ImageReader
        ir = ImageReader(path)
        iw, ih = ir.getSize()

        target_w = min(width * mm, max_w)
        scale = target_w / iw
        target_h = ih * scale

        if target_h > max_h:
            scale = max_h / ih
            target_w = iw * scale
            target_h = max_h

        img = Image(path, width=target_w, height=target_h)
        img.hAlign = "CENTER"
        result.append(img)
    except Exception:
        return result

    if caption:
        result.append(Spacer(1, 1 * mm))
        cap_style = ParagraphStyle("img_cap", parent=styles["caption"], alignment=TA_CENTER)
        result.append(Paragraph(_esc(caption), cap_style))

    result.append(Spacer(1, 3 * mm))
    return result


def _render_callout(sec, styles) -> list:
    title = sec.get("title", "")
    body = sec.get("body", "")
    result = []

    content = []
    if title:
        content.append(Paragraph(_esc(title), styles["callout_title"]))
    if body:
        content.append(Paragraph(_esc(body), styles["callout_body"]))

    if content:
        box = CalloutBox(content)
        result.append(KeepTogether([box]))
        result.append(Spacer(1, 3 * mm))
    return result


def _render_chart_bar(sec, styles) -> list:
    try:
        import matplotlib
        matplotlib.use("Agg")
        matplotlib.rcParams["font.sans-serif"] = [
            "WenQuanYi Micro Hei", "SimHei", "Noto Sans CJK SC",
            "Arial Unicode MS", "sans-serif",
        ]
        matplotlib.rcParams["axes.unicode_minus"] = False
        import matplotlib.pyplot as plt
        import numpy as np
    except ImportError:
        return []

    title = sec.get("title", "")
    cats = sec.get("categories", [])
    series = sec.get("series", [])
    if not cats or not series:
        return []

    n_cats = len(cats)
    for s in series:
        vals = s.get("values", [])
        if len(vals) != n_cats:
            min_len = min(len(vals), n_cats)
            s["values"] = vals[:min_len]
            cats = cats[:min_len]
    n_cats = len(cats)
    if n_cats == 0:
        return []

    palette = ["#1A365D", "#2B6CB0", "#38A169", "#D69E2E",
               "#E53E3E", "#805AD5", "#DD6B20"]

    fig, ax = plt.subplots(figsize=(6.5, 3))
    x = np.arange(n_cats)
    n = len(series)
    bw = 0.65 / max(n, 1)

    for i, s in enumerate(series):
        off = (i - n / 2 + 0.5) * bw
        ax.bar(x + off, s.get("values", []), bw,
               label=s.get("name", ""),
               color=palette[i % len(palette)],
               edgecolor="white", linewidth=0.5)

    ax.set_xticks(x)
    ax.set_xticklabels(cats, fontsize=8)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_color("#CBD5E0")
    ax.spines["bottom"].set_color("#CBD5E0")
    ax.tick_params(colors="#718096", labelsize=8)
    if title:
        ax.set_title(title, fontsize=11, fontweight="bold",
                     color="#1A365D", pad=8)
    if n > 1:
        ax.legend(fontsize=7, frameon=False)
    plt.tight_layout()

    tmp = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
    plt.savefig(tmp.name, dpi=180, bbox_inches="tight")
    plt.close()

    max_h = PAGE_H - MARGIN_T - MARGIN_B - 30 * mm

    result = []
    try:
        from reportlab.lib.utils import ImageReader
        ir = ImageReader(tmp.name)
        iw, ih = ir.getSize()
        target_w = min(150 * mm, CONTENT_W)
        scale = target_w / iw
        target_h = ih * scale
        if target_h > max_h:
            scale = max_h / ih
            target_w = iw * scale
            target_h = max_h
        img = Image(tmp.name, width=target_w, height=target_h)
        img.hAlign = "CENTER"
        result.append(img)
        _TEMP_CHART_FILES.append(tmp.name)
    except Exception:
        try:
            os.unlink(tmp.name)
        except OSError:
            pass

    result.append(Spacer(1, 4 * mm))
    return result


def _render_chart_pie(sec, styles) -> list:
    try:
        import matplotlib
        matplotlib.use("Agg")
        matplotlib.rcParams["font.sans-serif"] = [
            "WenQuanYi Micro Hei", "SimHei", "Noto Sans CJK SC",
            "Arial Unicode MS", "sans-serif",
        ]
        matplotlib.rcParams["axes.unicode_minus"] = False
        import matplotlib.pyplot as plt
    except ImportError:
        return []

    title = sec.get("title", "")
    labels = sec.get("labels", [])
    values = sec.get("values", [])
    if not labels or not values:
        return []

    if len(labels) != len(values):
        min_len = min(len(labels), len(values))
        labels = labels[:min_len]
        values = values[:min_len]
    if not labels:
        return []

    palette = ["#1A365D", "#2B6CB0", "#38A169", "#D69E2E",
               "#E53E3E", "#805AD5", "#DD6B20", "#319795",
               "#B83280", "#718096"]

    fig, ax = plt.subplots(figsize=(5, 3.5))
    colors = [palette[i % len(palette)] for i in range(len(labels))]
    wedges, texts, autotexts = ax.pie(
        values, labels=labels, colors=colors, autopct="%1.1f%%",
        startangle=90, pctdistance=0.75, textprops={"fontsize": 8},
    )
    for at in autotexts:
        at.set_fontsize(7)
        at.set_color("white")
    if title:
        ax.set_title(title, fontsize=11, fontweight="bold",
                     color="#1A365D", pad=10)
    plt.tight_layout()

    tmp = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
    plt.savefig(tmp.name, dpi=180, bbox_inches="tight")
    plt.close()

    max_h = PAGE_H - MARGIN_T - MARGIN_B - 30 * mm
    result = []
    try:
        from reportlab.lib.utils import ImageReader
        ir = ImageReader(tmp.name)
        iw, ih = ir.getSize()
        target_w = min(120 * mm, CONTENT_W)
        scale = target_w / iw
        target_h = ih * scale
        if target_h > max_h:
            scale = max_h / ih
            target_w = iw * scale
            target_h = max_h
        img = Image(tmp.name, width=target_w, height=target_h)
        img.hAlign = "CENTER"
        result.append(img)
        _TEMP_CHART_FILES.append(tmp.name)
    except Exception:
        try:
            os.unlink(tmp.name)
        except OSError:
            pass

    result.append(Spacer(1, 4 * mm))
    return result


def _render_chart_line(sec, styles) -> list:
    try:
        import matplotlib
        matplotlib.use("Agg")
        matplotlib.rcParams["font.sans-serif"] = [
            "WenQuanYi Micro Hei", "SimHei", "Noto Sans CJK SC",
            "Arial Unicode MS", "sans-serif",
        ]
        matplotlib.rcParams["axes.unicode_minus"] = False
        import matplotlib.pyplot as plt
    except ImportError:
        return []

    title = sec.get("title", "")
    x_labels = sec.get("x_labels", [])
    series = sec.get("series", [])
    x_title = sec.get("x_title", "")
    y_title = sec.get("y_title", "")
    if not x_labels or not series:
        return []

    n_x = len(x_labels)
    for s in series:
        vals = s.get("values", [])
        if len(vals) != n_x:
            min_len = min(len(vals), n_x)
            s["values"] = vals[:min_len]
            x_labels = x_labels[:min_len]
    n_x = len(x_labels)
    if n_x == 0:
        return []

    palette = ["#1A365D", "#2B6CB0", "#38A169", "#D69E2E",
               "#E53E3E", "#805AD5", "#DD6B20"]

    fig, ax = plt.subplots(figsize=(6.5, 3))
    for i, s in enumerate(series):
        vals = s.get("values", [])
        ax.plot(range(len(vals)), vals,
                marker="o", markersize=4, linewidth=1.8,
                label=s.get("name", ""),
                color=palette[i % len(palette)])

    ax.set_xticks(range(n_x))
    ax.set_xticklabels(x_labels, fontsize=8)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_color("#CBD5E0")
    ax.spines["bottom"].set_color("#CBD5E0")
    ax.tick_params(colors="#718096", labelsize=8)
    ax.grid(axis="y", linestyle="--", alpha=0.3)
    if x_title:
        ax.set_xlabel(x_title, fontsize=9, color="#4A5568")
    if y_title:
        ax.set_ylabel(y_title, fontsize=9, color="#4A5568")
    if title:
        ax.set_title(title, fontsize=11, fontweight="bold",
                     color="#1A365D", pad=8)
    if len(series) > 1:
        ax.legend(fontsize=7, frameon=False)
    plt.tight_layout()

    tmp = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
    plt.savefig(tmp.name, dpi=180, bbox_inches="tight")
    plt.close()

    max_h = PAGE_H - MARGIN_T - MARGIN_B - 30 * mm
    result = []
    try:
        from reportlab.lib.utils import ImageReader
        ir = ImageReader(tmp.name)
        iw, ih = ir.getSize()
        target_w = min(150 * mm, CONTENT_W)
        scale = target_w / iw
        target_h = ih * scale
        if target_h > max_h:
            scale = max_h / ih
            target_w = iw * scale
            target_h = max_h
        img = Image(tmp.name, width=target_w, height=target_h)
        img.hAlign = "CENTER"
        result.append(img)
        _TEMP_CHART_FILES.append(tmp.name)
    except Exception:
        try:
            os.unlink(tmp.name)
        except OSError:
            pass

    result.append(Spacer(1, 4 * mm))
    return result


def _render_references(sec, styles) -> list:
    items = sec.get("items", [])
    heading = sec.get("heading", None)
    show_heading = sec.get("show_heading", heading is not None)
    result = []

    if show_heading:
        h = heading or "References"
        result.append(DividerLine())
        result.append(Spacer(1, 2 * mm))
        para = HeadingParagraph(_esc(h), styles["h1"], level=0, toc_text=h)
        result.append(LeftBarParagraph(para))
        result.append(AccentLine(width=40 * mm))
        result.append(Spacer(1, 3 * mm))

    for i, ref in enumerate(items):
        anchor = f'<a name="ref_{i + 1}"/>'
        if isinstance(ref, dict):
            ref_str = ref.get("text", ref.get("content", "")).strip()
        else:
            ref_str = str(ref).strip()
        ref_str = re.sub(r'^\[\d+\]\s*', '', ref_str)
        label = f'<font color="#{_color_hex(NAVY)}"><b>[{i + 1}]</b></font>&nbsp;&nbsp;'
        text = anchor + label + _esc(ref_str)
        result.append(Paragraph(text, styles["ref"]))

    result.append(Spacer(1, 3 * mm))
    return result


def _render_page_break(sec, styles) -> list:
    return [PageBreak()]


# ---------------------------------------------------------------------------
# Section dispatch
# ---------------------------------------------------------------------------

_TEMP_CHART_FILES: list[str] = []

_RENDERERS = {
    "heading": _render_heading,
    "text": _render_text,
    "bullets": _render_bullets,
    "table": _render_table,
    "kv": _render_kv,
    "image": _render_image,
    "callout": _render_callout,
    "chart_bar": _render_chart_bar,
    "chart_pie": _render_chart_pie,
    "chart_line": _render_chart_line,
    "references": _render_references,
    "page_break": _render_page_break,
}


# ---------------------------------------------------------------------------
# Build the report
# ---------------------------------------------------------------------------

def build_report(data: dict, output_path: str):
    """Build the PDF report from JSON data."""
    all_text = json.dumps(data, ensure_ascii=False)
    if _has_cjk(all_text):
        _register_cjk_fonts()

    styles = _build_styles()

    global _AVAILABLE_REF_COUNT
    _AVAILABLE_REF_COUNT = 0
    for sec in data.get("sections", []):
        if sec.get("type") == "references":
            _AVAILABLE_REF_COUNT += len(sec.get("items", []))

    # --- Page templates ---
    content_frame = Frame(
        MARGIN_L, MARGIN_B, CONTENT_W, PAGE_H - MARGIN_T - MARGIN_B,
        id="content",
    )
    cover_frame = Frame(0, 0, PAGE_W, PAGE_H, id="cover")

    cover_template = PageTemplate(
        id="cover", frames=[cover_frame], onPage=_draw_cover,
    )
    toc_template = PageTemplate(
        id="toc", frames=[content_frame], onPage=_draw_toc_header,
    )
    content_template = PageTemplate(
        id="content", frames=[content_frame], onPage=_draw_header_footer,
    )

    doc = ReportDocTemplate(
        output_path,
        report_data=data,
        pagesize=A4,
        pageTemplates=[cover_template, toc_template, content_template],
    )

    # --- Build story ---
    story = []

    # Cover page (empty flowable — actual drawing done by onPage callback)
    story.append(NextPageTemplate("toc"))
    story.append(PageBreak())

    # TOC page
    show_toc = data.get("toc", True)
    if show_toc:
        toc_title = Paragraph(_esc("Table of Contents"), styles["h1"])
        story.append(toc_title)
        story.append(Spacer(1, 2 * mm))
        story.append(AccentLine(width=40 * mm))
        story.append(Spacer(1, 4 * mm))

        doc._toc.levelStyles = [styles["toc_h1"], styles["toc_h2"], styles["toc_h3"]]
        story.append(doc._toc)

        story.append(NextPageTemplate("content"))
        story.append(PageBreak())
    else:
        story.append(NextPageTemplate("content"))
        story.append(PageBreak())

    # Content sections
    for sec in data.get("sections", []):
        renderer = _RENDERERS.get(sec.get("type", ""))
        if renderer:
            flowables = renderer(sec, styles)
            story.extend(flowables)

    # Build (multiBuild for TOC page number resolution)
    doc.multiBuild(story)

    for tmp_path in _TEMP_CHART_FILES:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
    _TEMP_CHART_FILES.clear()

    page_count = doc.page
    print(f"Report generated: {output_path}")
    print(f"  Title : {data.get('title', 'N/A')}")
    print(f"  Pages : {page_count}")
    print(f"  TOC   : {'yes' if show_toc else 'no'}")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    data_path = sys.argv[1]
    output_path = sys.argv[2] if len(sys.argv) >= 3 else "report.pdf"

    with open(data_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    build_report(data, output_path)


if __name__ == "__main__":
    main()
