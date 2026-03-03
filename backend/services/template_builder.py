"""
Build the Constellation Capital AG One-Pager PPTX template programmatically.

This creates a single-slide template with all named shapes positioned
in the correct grid layout. The template is generated once and reused
by the PPTX generator.
"""

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.util import Inches, Pt, Emu
from pptx.oxml.ns import qn
import os

# Constellation Capital brand colors
DARK_BLUE = RGBColor(0x1F, 0x4E, 0x79)
MID_BLUE = RGBColor(0x2E, 0x75, 0xB6)
LIGHT_BLUE = RGBColor(0xBD, 0xD7, 0xEE)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
BLACK = RGBColor(0x00, 0x00, 0x00)
DARK_GRAY = RGBColor(0x40, 0x40, 0x40)
LIGHT_GRAY = RGBColor(0xD9, 0xD9, 0xD9)
GREEN = RGBColor(0x00, 0xB0, 0x50)
RED = RGBColor(0xFF, 0x00, 0x00)
YELLOW = RGBColor(0xFF, 0xC0, 0x00)

# Slide dimensions (Widescreen 16:9)
SLIDE_WIDTH = Inches(13.333)
SLIDE_HEIGHT = Inches(7.5)

# Layout constants
MARGIN_LEFT = Inches(0.3)
MARGIN_TOP = Inches(0.9)
COL_GAP = Inches(0.15)
ROW_GAP = Inches(0.1)

# Column widths (3-column layout)
COL1_WIDTH = Inches(3.8)
COL2_WIDTH = Inches(4.4)
COL3_WIDTH = Inches(4.4)

COL1_LEFT = MARGIN_LEFT
COL2_LEFT = COL1_LEFT + COL1_WIDTH + COL_GAP
COL3_LEFT = COL2_LEFT + COL2_WIDTH + COL_GAP


def _add_textbox(slide, name, left, top, width, height):
    """Add a named text box to the slide."""
    txBox = slide.shapes.add_textbox(left, top, width, height)
    txBox.name = name
    return txBox


def _set_text(shape, text, font_name="Calibri", font_size=Pt(9),
              bold=False, color=DARK_GRAY, alignment=PP_ALIGN.LEFT):
    """Set text with formatting on a shape."""
    tf = shape.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.alignment = alignment
    run = p.add_run()
    run.text = text
    run.font.name = font_name
    run.font.size = font_size
    run.font.bold = bold
    run.font.color.rgb = color
    return tf


def _add_section_header(slide, name, text, left, top, width, height=Inches(0.3)):
    """Add a dark-blue section header bar."""
    shape = slide.shapes.add_shape(
        1,  # MSO_SHAPE.RECTANGLE
        left, top, width, height
    )
    shape.name = name
    shape.fill.solid()
    shape.fill.fore_color.rgb = DARK_BLUE
    shape.line.fill.background()

    tf = shape.text_frame
    tf.word_wrap = True
    tf.margin_left = Pt(4)
    tf.margin_top = Pt(2)
    tf.margin_bottom = Pt(2)
    p = tf.paragraphs[0]
    p.alignment = PP_ALIGN.LEFT
    run = p.add_run()
    run.text = text
    run.font.name = "Calibri"
    run.font.size = Pt(9)
    run.font.bold = True
    run.font.color.rgb = WHITE
    return shape


def _add_criteria_row(slide, name_prefix, label, left, top, width, row_height=Inches(0.2)):
    """Add a criterion row with label and status indicator placeholder."""
    # Label text
    label_box = _add_textbox(slide, f"{name_prefix}_label", left, top, width * 0.75, row_height)
    tf = label_box.text_frame
    tf.margin_left = Pt(2)
    tf.margin_top = Pt(0)
    tf.margin_bottom = Pt(0)
    p = tf.paragraphs[0]
    run = p.add_run()
    run.text = label
    run.font.name = "Calibri"
    run.font.size = Pt(7)
    run.font.color.rgb = DARK_GRAY

    # Status indicator (small rectangle)
    indicator = slide.shapes.add_shape(
        1,  # RECTANGLE
        left + width * 0.78, top + Emu(10000),
        Inches(0.15), Inches(0.15)
    )
    indicator.name = f"{name_prefix}_status"
    indicator.fill.solid()
    indicator.fill.fore_color.rgb = LIGHT_GRAY
    indicator.line.fill.background()
    return label_box, indicator


def build_template(output_path: str):
    """Build the complete One-Pager template PPTX."""
    prs = Presentation()
    prs.slide_width = SLIDE_WIDTH
    prs.slide_height = SLIDE_HEIGHT

    # Use blank layout
    blank_layout = prs.slide_layouts[6]
    slide = prs.slides.add_slide(blank_layout)

    # ══════════════════════════════════════════════
    # HEADER BAR (top of slide)
    # ══════════════════════════════════════════════
    header_bar = slide.shapes.add_shape(
        1, Inches(0), Inches(0), SLIDE_WIDTH, Inches(0.75)
    )
    header_bar.name = "header_bar"
    header_bar.fill.solid()
    header_bar.fill.fore_color.rgb = DARK_BLUE
    header_bar.line.fill.background()

    # "One Pager" label
    label_box = _add_textbox(slide, "header_label", Inches(0.3), Inches(0.1), Inches(2), Inches(0.3))
    _set_text(label_box, "One Pager", font_size=Pt(14), bold=True, color=WHITE)

    # Company name
    company_box = _add_textbox(slide, "header_company", Inches(0.3), Inches(0.35), Inches(6), Inches(0.35))
    _set_text(company_box, "COMPANY NAME", font_size=Pt(18), bold=True, color=WHITE)

    # Tagline / Investment thesis (right side of header)
    tagline_box = _add_textbox(slide, "header_tagline", Inches(6.5), Inches(0.15), Inches(6.5), Inches(0.5))
    tf = _set_text(tagline_box, "Investment thesis / tagline",
                   font_size=Pt(10), color=WHITE, alignment=PP_ALIGN.RIGHT)

    # Logo placeholder (top-right corner)
    logo_box = _add_textbox(slide, "logo_placeholder", Inches(12.0), Inches(0.1), Inches(1.1), Inches(0.55))
    _set_text(logo_box, "LOGO", font_size=Pt(8), color=RGBColor(0x80, 0x80, 0x80),
              alignment=PP_ALIGN.CENTER)

    # ══════════════════════════════════════════════
    # COLUMN 1: Key Facts + Status
    # ══════════════════════════════════════════════
    col1_top = MARGIN_TOP

    # Key Facts header
    _add_section_header(slide, "keyfacts_header", "Key Facts",
                        COL1_LEFT, col1_top, COL1_WIDTH)

    # Key Facts content
    kf_top = col1_top + Inches(0.35)
    kf_box = _add_textbox(slide, "keyfacts_content",
                           COL1_LEFT, kf_top, COL1_WIDTH, Inches(2.8))
    tf = kf_box.text_frame
    tf.word_wrap = True
    tf.margin_left = Pt(4)
    tf.margin_top = Pt(4)

    # Key facts fields as placeholder text
    fields = [
        ("Founded:", ""),
        ("HQ:", ""),
        ("Website:", ""),
        ("Industry:", ""),
        ("Niche:", ""),
        ("Revenue:", ""),
        ("EBITDA:", ""),
        ("Management:", ""),
        ("Employees:", ""),
    ]
    for i, (label, value) in enumerate(fields):
        if i > 0:
            p = tf.add_paragraph()
        else:
            p = tf.paragraphs[0]
        p.space_before = Pt(2)
        p.space_after = Pt(1)

        label_run = p.add_run()
        label_run.text = label + " "
        label_run.font.name = "Calibri"
        label_run.font.size = Pt(8)
        label_run.font.bold = True
        label_run.font.color.rgb = DARK_BLUE

        value_run = p.add_run()
        value_run.text = value
        value_run.font.name = "Calibri"
        value_run.font.size = Pt(8)
        value_run.font.color.rgb = DARK_GRAY

    # Investment Criteria section
    criteria_top = kf_top + Inches(2.9)
    _add_section_header(slide, "criteria_header", "Investment Criteria",
                        COL1_LEFT, criteria_top, COL1_WIDTH)

    criteria_items = [
        ("criteria_ebitda_1m", "EBITDA (EUR 1.0m)"),
        ("criteria_dach", "DACH"),
        ("criteria_ebitda_margin_10", "EBITDA Margin (10%)"),
        ("criteria_majority_stake", "Majority Stake"),
        ("criteria_revenue_split", "Revenue Split"),
        ("criteria_digitization", "Digitization Potential"),
        ("criteria_asset_light", "Asset Light"),
        ("criteria_buy_and_build", "Buy & Build Potential"),
        ("criteria_esg", "ESG"),
        ("criteria_market_fragmentation", "Market Fragmentation"),
        ("criteria_acquisition_vertical", "Acquisition: Vertical"),
        ("criteria_acquisition_horizontal", "Acquisition: Horizontal"),
        ("criteria_acquisition_geographical", "Acquisition: Geographical"),
    ]

    row_top = criteria_top + Inches(0.35)
    for name_prefix, label in criteria_items:
        _add_criteria_row(slide, name_prefix, label,
                         COL1_LEFT, row_top, COL1_WIDTH)
        row_top += Inches(0.22)

    # Status section (bottom of column 1)
    status_top = row_top + Inches(0.1)
    _add_section_header(slide, "status_header", "Status",
                        COL1_LEFT, status_top, COL1_WIDTH)

    status_box = _add_textbox(slide, "status_content",
                               COL1_LEFT, status_top + Inches(0.35),
                               COL1_WIDTH, Inches(0.7))
    tf = status_box.text_frame
    tf.word_wrap = True
    tf.margin_left = Pt(4)
    p = tf.paragraphs[0]
    run = p.add_run()
    run.text = "Source: \nIM received: \nLOI Deadline: \nStatus: "
    run.font.name = "Calibri"
    run.font.size = Pt(8)
    run.font.color.rgb = DARK_GRAY

    # ══════════════════════════════════════════════
    # COLUMN 2: Description + Product Portfolio + Revenue Split
    # ══════════════════════════════════════════════
    col2_top = MARGIN_TOP

    # Description header
    _add_section_header(slide, "description_header", "Description",
                        COL2_LEFT, col2_top, COL2_WIDTH)

    # Description content
    desc_box = _add_textbox(slide, "description_content",
                             COL2_LEFT, col2_top + Inches(0.35),
                             COL2_WIDTH, Inches(1.6))
    tf = desc_box.text_frame
    tf.word_wrap = True
    tf.margin_left = Pt(4)
    p = tf.paragraphs[0]
    run = p.add_run()
    run.text = "• Description bullet points"
    run.font.name = "Calibri"
    run.font.size = Pt(8)
    run.font.color.rgb = DARK_GRAY

    # Product Portfolio header
    pp_top = col2_top + Inches(2.05)
    _add_section_header(slide, "portfolio_header", "Product Portfolio",
                        COL2_LEFT, pp_top, COL2_WIDTH)

    # Product Portfolio content
    pp_box = _add_textbox(slide, "portfolio_content",
                           COL2_LEFT, pp_top + Inches(0.35),
                           COL2_WIDTH, Inches(1.4))
    tf = pp_box.text_frame
    tf.word_wrap = True
    tf.margin_left = Pt(4)
    p = tf.paragraphs[0]
    run = p.add_run()
    run.text = "• Product portfolio bullet points"
    run.font.name = "Calibri"
    run.font.size = Pt(8)
    run.font.color.rgb = DARK_GRAY

    # Revenue Split header
    rs_top = pp_top + Inches(1.85)
    _add_section_header(slide, "revsplit_header", "Revenue Split",
                        COL2_LEFT, rs_top, COL2_WIDTH)

    # Revenue Split chart placeholder
    chart_placeholder = _add_textbox(slide, "revsplit_chart",
                                      COL2_LEFT + Inches(0.2), rs_top + Inches(0.4),
                                      COL2_WIDTH - Inches(0.4), Inches(2.2))
    _set_text(chart_placeholder, "[Revenue Split Chart]",
              font_size=Pt(10), color=LIGHT_GRAY, alignment=PP_ALIGN.CENTER)

    # ══════════════════════════════════════════════
    # COLUMN 3: Investment Rationale + Key Financials
    # ══════════════════════════════════════════════
    col3_top = MARGIN_TOP

    # Investment Rationale header
    _add_section_header(slide, "rationale_header", "Investment Rationale",
                        COL3_LEFT, col3_top, COL3_WIDTH)

    # Pros section
    pros_box = _add_textbox(slide, "rationale_pros",
                             COL3_LEFT, col3_top + Inches(0.35),
                             COL3_WIDTH, Inches(1.2))
    tf = pros_box.text_frame
    tf.word_wrap = True
    tf.margin_left = Pt(4)
    p = tf.paragraphs[0]
    run = p.add_run()
    run.text = "✅ Pros"
    run.font.name = "Calibri"
    run.font.size = Pt(8)
    run.font.color.rgb = GREEN

    # Cons section
    cons_box = _add_textbox(slide, "rationale_cons",
                             COL3_LEFT, col3_top + Inches(1.6),
                             COL3_WIDTH, Inches(1.0))
    tf = cons_box.text_frame
    tf.word_wrap = True
    tf.margin_left = Pt(4)
    p = tf.paragraphs[0]
    run = p.add_run()
    run.text = "❌ Cons"
    run.font.name = "Calibri"
    run.font.size = Pt(8)
    run.font.color.rgb = RED

    # Key Financials header
    fin_top = col3_top + Inches(2.7)
    _add_section_header(slide, "financials_header", "Key Financials",
                        COL3_LEFT, fin_top, COL3_WIDTH)

    # Key Financials chart placeholder
    fin_chart = _add_textbox(slide, "financials_chart",
                              COL3_LEFT + Inches(0.2), fin_top + Inches(0.4),
                              COL3_WIDTH - Inches(0.4), Inches(2.8))
    _set_text(fin_chart, "[Key Financials Chart]",
              font_size=Pt(10), color=LIGHT_GRAY, alignment=PP_ALIGN.CENTER)

    # ══════════════════════════════════════════════
    # FOOTER
    # ══════════════════════════════════════════════
    footer_box = _add_textbox(slide, "footer",
                               Inches(0.3), Inches(7.1),
                               Inches(5), Inches(0.3))
    _set_text(footer_box, "Strictly Private & Confidential",
              font_size=Pt(7), color=DARK_GRAY, alignment=PP_ALIGN.LEFT)

    # Save
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    prs.save(output_path)
    return output_path


if __name__ == "__main__":
    path = build_template(
        os.path.join(os.path.dirname(__file__), "..", "template", "one_pager_template.pptx")
    )
    print(f"Template saved to: {path}")
