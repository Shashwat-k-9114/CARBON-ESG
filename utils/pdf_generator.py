"""
Carbon ESG Platform — Premium PDF Report Generator
Produces beautiful, professional PDFs for carbon reports, ESG assessments, and certificates.
"""

from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, cm, mm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    Flowable, KeepTogether, PageBreak
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.graphics.shapes import (
    Drawing, Line, Rect, Circle, String, Polygon, Path
)
from reportlab.graphics import renderPDF
from datetime import datetime
import os
import math

# ── Font Registration ──────────────────────────────────────────────────────────
try:
    pdfmetrics.registerFont(TTFont('Roboto-Light',   'Roboto-Light.ttf'))
    pdfmetrics.registerFont(TTFont('Roboto-Regular', 'Roboto-Regular.ttf'))
    pdfmetrics.registerFont(TTFont('Roboto-Medium',  'Roboto-Medium.ttf'))
    pdfmetrics.registerFont(TTFont('Roboto-Bold',    'Roboto-Bold.ttf'))
    FONT_LIGHT   = 'Roboto-Light'
    FONT_REGULAR = 'Roboto-Regular'
    FONT_MEDIUM  = 'Roboto-Medium'
    FONT_BOLD    = 'Roboto-Bold'
except Exception:
    FONT_LIGHT   = 'Helvetica'
    FONT_REGULAR = 'Helvetica'
    FONT_MEDIUM  = 'Helvetica-Bold'
    FONT_BOLD    = 'Helvetica-Bold'

# ── Brand Colours ──────────────────────────────────────────────────────────────
C = {
    'forest':    colors.HexColor('#0D2818'),
    'primary':   colors.HexColor('#155724'),
    'mid':       colors.HexColor('#1a6b35'),
    'emerald':   colors.HexColor('#2ecc71'),
    'mint':      colors.HexColor('#a8e6cf'),
    'sage':      colors.HexColor('#E8F5E9'),
    'sage2':     colors.HexColor('#C8E6C9'),
    'blue':      colors.HexColor('#0d47a1'),
    'sky':       colors.HexColor('#42a5f5'),
    'navy':      colors.HexColor('#0a1428'),
    'amber':     colors.HexColor('#b7791f'),
    'gold':      colors.HexColor('#f6d860'),
    'gold2':     colors.HexColor('#ffd700'),
    'cream':     colors.HexColor('#fdfaf4'),
    'parchment': colors.HexColor('#f5efe0'),
    'warning':   colors.HexColor('#ff9800'),
    'danger':    colors.HexColor('#ef5350'),
    'white':     colors.white,
    'black':     colors.HexColor('#1c1c1e'),
    'gray1':     colors.HexColor('#f5f5f5'),
    'gray2':     colors.HexColor('#e0e0e0'),
    'gray3':     colors.HexColor('#9e9e9e'),
    'text':      colors.HexColor('#2c2c2e'),
    'muted':     colors.HexColor('#6c6c70'),
}


# ── Custom Flowables ───────────────────────────────────────────────────────────

class FullWidthRect(Flowable):
    """A decorative full-width coloured rectangle."""
    def __init__(self, height, fill_color, stroke=False):
        Flowable.__init__(self)
        self.height = height
        self.fill_color = fill_color
        self.stroke = stroke
        self.width = 0  # set on draw

    def draw(self):
        self.canv.setFillColor(self.fill_color)
        self.canv.rect(0, 0, self.width or 500, self.height, stroke=0, fill=1)


class GradientBar(Flowable):
    """Horizontal gradient bar — used as section dividers."""
    def __init__(self, width, height=4, c1=None, c2=None):
        Flowable.__init__(self)
        self.width  = width
        self.height = height
        self.c1 = c1 or C['primary']
        self.c2 = c2 or C['emerald']

    def draw(self):
        steps = 40
        for i in range(steps):
            x   = (i / steps) * self.width
            w   = self.width / steps + 1
            t   = i / steps
            r   = self.c1.red   + (self.c2.red   - self.c1.red)   * t
            g   = self.c1.green + (self.c2.green - self.c1.green) * t
            b   = self.c1.blue  + (self.c2.blue  - self.c1.blue)  * t
            self.canv.setFillColor(colors.Color(r, g, b))
            self.canv.rect(x, 0, w, self.height, stroke=0, fill=1)


class SectionDivider(Flowable):
    """Thin elegant divider with optional label."""
    def __init__(self, width, label='', color=None):
        Flowable.__init__(self)
        self.width = width
        self.label = label
        self.color = color or C['gray2']

    def draw(self):
        self.canv.setStrokeColor(self.color)
        self.canv.setLineWidth(0.5)
        self.canv.line(0, 2, self.width, 2)


class ScoreGauge(Flowable):
    """
    Beautiful arc-gauge showing a score 0–100.
    centre_x, centre_y = position within drawing
    """
    def __init__(self, score, width=200, height=120, color=None):
        Flowable.__init__(self)
        self.score  = max(0, min(100, score))
        self.width  = width
        self.height = height
        self.color  = color

    def draw(self):
        cx = self.width / 2
        cy = 30
        r  = 70
        canv = self.canv

        # Background arc (grey)
        canv.setStrokeColor(C['gray2'])
        canv.setLineWidth(14)
        canv.arc(cx - r, cy - r, cx + r, cy + r, startAng=0, extent=180)

        # Score arc (coloured)
        if self.score > 0:
            sc = self.color or (
                C['emerald'] if self.score >= 70 else
                C['warning'] if self.score >= 40 else
                C['danger']
            )
            canv.setStrokeColor(sc)
            canv.setLineWidth(14)
            extent = (self.score / 100) * 180
            canv.arc(cx - r, cy - r, cx + r, cy + r, startAng=0, extent=extent)

        # Score number
        canv.setFillColor(C['black'])
        canv.setFont(FONT_BOLD, 32)
        canv.drawCentredString(cx, cy - 10, str(int(self.score)))

        # /100 label
        canv.setFillColor(C['muted'])
        canv.setFont(FONT_REGULAR, 10)
        canv.drawCentredString(cx, cy - 26, '/ 100')


class CertificateBorder(Flowable):
    """Elegant decorative border for certificate page."""
    def __init__(self, width, height, color=None, accent=None):
        Flowable.__init__(self)
        self.width  = width
        self.height = height
        self.color  = color  or C['amber']
        self.accent = accent or C['gold2']

    def draw(self):
        canv  = self.canv
        w, h  = self.width, self.height
        m     = 8    # margin
        r     = 16   # corner radius
        lw    = 2.5

        # Outer border
        canv.setStrokeColor(self.color)
        canv.setLineWidth(lw)
        canv.roundRect(m, m, w - 2*m, h - 2*m, r, stroke=1, fill=0)

        # Inner border (thin, inset)
        canv.setStrokeColor(self.accent)
        canv.setLineWidth(0.8)
        canv.roundRect(m + 7, m + 7, w - 2*(m+7), h - 2*(m+7), r - 3, stroke=1, fill=0)

        # Corner ornament squares
        cs = 10
        for x, y in [(m, m), (w-m-cs, m), (m, h-m-cs), (w-m-cs, h-m-cs)]:
            canv.setFillColor(self.color)
            canv.rect(x, y, cs, cs, stroke=0, fill=1)


class GoldSeal(Flowable):
    """Circular gold seal / stamp for certificate."""
    def __init__(self, size=80):
        Flowable.__init__(self)
        self.size   = size
        self.width  = size
        self.height = size

    def draw(self):
        canv = self.canv
        cx   = self.size / 2
        cy   = self.size / 2
        r    = self.size / 2 - 4

        # Outer circle
        canv.setFillColor(C['gold2'])
        canv.setStrokeColor(C['amber'])
        canv.setLineWidth(2)
        canv.circle(cx, cy, r, stroke=1, fill=1)

        # Inner ring
        canv.setFillColor(C['amber'])
        canv.setStrokeColor(colors.white)
        canv.setLineWidth(1.5)
        canv.circle(cx, cy, r - 8, stroke=1, fill=0)

        # Star / asterisk in centre
        canv.setFillColor(C['amber'])
        canv.setFont(FONT_BOLD, 20)
        canv.drawCentredString(cx, cy - 7, '★')


# ── Page Callbacks ─────────────────────────────────────────────────────────────

def _header_footer_carbon(canvas, doc):
    """Carbon report header/footer drawn on every page."""
    canvas.saveState()
    w, h = A4

    # Top bar
    canvas.setFillColor(C['forest'])
    canvas.rect(0, h - 44, w, 44, stroke=0, fill=1)

    # Brand name
    canvas.setFillColor(colors.white)
    canvas.setFont(FONT_BOLD, 11)
    canvas.drawString(36, h - 28, 'Carbon.ESG')

    canvas.setFillColor(colors.HexColor('#2ecc71'))
    canvas.setFont(FONT_REGULAR, 9)
    canvas.drawRightString(w - 36, h - 28, 'Carbon Footprint Report  |  Confidential')

    # Bottom bar
    canvas.setFillColor(C['sage'])
    canvas.rect(0, 0, w, 32, stroke=0, fill=1)

    canvas.setFillColor(C['muted'])
    canvas.setFont(FONT_REGULAR, 8)
    canvas.drawString(36, 10, f'Generated: {datetime.now().strftime("%d %B %Y, %H:%M")}')
    canvas.drawRightString(w - 36, 10, f'Page {doc.page}  |  Carbon ESG Platform')

    # Thin gradient top accent
    steps = 30
    bw = w / steps
    for i in range(steps):
        t = i / steps
        r = C['primary'].red + (C['emerald'].red - C['primary'].red) * t
        g = C['primary'].green + (C['emerald'].green - C['primary'].green) * t
        b = C['primary'].blue + (C['emerald'].blue - C['primary'].blue) * t
        canvas.setFillColor(colors.Color(r, g, b))
        canvas.rect(i * bw, h - 48, bw + 1, 4, stroke=0, fill=1)

    canvas.restoreState()


def _header_footer_esg(canvas, doc):
    """ESG report header/footer."""
    canvas.saveState()
    w, h = A4

    canvas.setFillColor(C['navy'])
    canvas.rect(0, h - 44, w, 44, stroke=0, fill=1)

    canvas.setFillColor(colors.white)
    canvas.setFont(FONT_BOLD, 11)
    canvas.drawString(36, h - 28, 'Carbon.ESG')

    canvas.setFillColor(C['sky'])
    canvas.setFont(FONT_REGULAR, 9)
    canvas.drawRightString(w - 36, h - 28, 'ESG Readiness Report  |  Confidential')

    canvas.setFillColor(colors.HexColor('#f0f6ff'))
    canvas.rect(0, 0, w, 32, stroke=0, fill=1)

    canvas.setFillColor(C['muted'])
    canvas.setFont(FONT_REGULAR, 8)
    canvas.drawString(36, 10, f'Generated: {datetime.now().strftime("%d %B %Y, %H:%M")}')
    canvas.drawRightString(w - 36, 10, f'Page {doc.page}  |  Carbon ESG Platform')

    steps = 30
    bw = w / steps
    for i in range(steps):
        t = i / steps
        r = C['blue'].red + (C['sky'].red - C['blue'].red) * t
        g = C['blue'].green + (C['sky'].green - C['blue'].green) * t
        b = C['blue'].blue + (C['sky'].blue - C['blue'].blue) * t
        canvas.setFillColor(colors.Color(r, g, b))
        canvas.rect(i * bw, h - 48, bw + 1, 4, stroke=0, fill=1)

    canvas.restoreState()


# ── Helper: build paragraph style dict ────────────────────────────────────────

def _s(name, base='Normal', font=None, size=10, color=None, align=TA_LEFT,
       leading=None, before=0, after=8, bold=False):
    """Create a paragraph style - FIXED: removed fontName parameter"""
    font_name = font or (FONT_BOLD if bold else FONT_REGULAR)
    return ParagraphStyle(
        name=name,
        parent=getSampleStyleSheet()[base],
        fontName=font_name,
        fontSize=size,
        textColor=color or C['text'],
        alignment=align,
        leading=leading or size * 1.4,
        spaceBefore=before,
        spaceAfter=after,
    )


# ── PDF Generator ──────────────────────────────────────────────────────────────

class PDFGenerator:

    # ── Carbon Footprint Report ────────────────────────────────────────────────

    def generate_individual_report(self, user_data: dict, assessment_data: dict, recommendations=None) -> str:
        """
        Generate a beautiful, professional Carbon Footprint Report.
        """
        if recommendations is None:
            recommendations = assessment_data.get('suggestions', [])
        
        # Convert to list if it's not already a list
        if not isinstance(recommendations, list):
            if isinstance(recommendations, dict):
                recommendations = list(recommendations.values())
            else:
                recommendations = []
            
        filename  = f"carbon_report_{user_data['username']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        filepath  = os.path.join('static', 'reports', filename)
        os.makedirs(os.path.dirname(filepath), exist_ok=True)

        doc = SimpleDocTemplate(
            filepath, pagesize=A4,
            rightMargin=36, leftMargin=36,
            topMargin=60, bottomMargin=48,
            title='Carbon Footprint Report',
            author='Carbon ESG Platform',
        )

        story = []
        W = A4[0] - 72   # usable width

        # ── STYLES ────────────────────────────────────────────────────────────
        sTitle    = _s('Title',    size=26, color=C['forest'], align=TA_CENTER, bold=True, leading=32, after=4)
        sSub      = _s('Sub',      size=12, color=C['mid'],    align=TA_CENTER, leading=16, after=20)
        sSec      = _s('Sec',      size=14, color=C['primary'], bold=True, before=6, after=10)
        sBody     = _s('Body',     size=10, color=C['text'],   leading=15, after=8)
        sSmall    = _s('Small',    size=8,  color=C['muted'],  align=TA_CENTER, after=4)
        sLabel    = _s('Label',    size=8,  color=C['muted'],  bold=True, after=2)
        sVal      = _s('Val',      size=11, color=C['black'],  bold=True, after=0)
        sRec      = _s('Rec',      size=9,  color=C['text'],   leading=14, after=6)
        sTH       = _s('TH',       size=9,  color=colors.white, align=TA_CENTER, bold=True)
        sTD       = _s('TD',       size=9,  color=C['text'],   align=TA_CENTER, leading=13)
        sTDL      = _s('TDL',      size=9,  color=C['text'],   align=TA_LEFT,   leading=13)

        footprint = assessment_data.get('total_footprint', 0)
        level     = assessment_data.get('carbon_level', 'Medium')
        username  = user_data.get('username', 'User')

        level_color = C['emerald'] if level == 'Low' else C['warning'] if level == 'Medium' else C['danger']

        # ── COVER BLOCK ───────────────────────────────────────────────────────
        story.append(Spacer(1, 10))
        story.append(GradientBar(W, 6, C['primary'], C['emerald']))
        story.append(Spacer(1, 24))

        story.append(Paragraph('Carbon Footprint Report', sTitle))
        story.append(Paragraph(f'Prepared for <b>{username}</b>', sSub))

        # Hero metric table
        hero_data = [
            [
                Paragraph(f'<b>{int(footprint):,}</b>', _s('H1', size=28, color=level_color, align=TA_CENTER, bold=True, leading=32)),
                Paragraph(f'<b>{level}</b>', _s('H2', size=22, color=level_color, align=TA_CENTER, bold=True, leading=26)),
                Paragraph(f'<b>{datetime.now().strftime("%Y")}</b>', _s('H3', size=22, color=C['forest'], align=TA_CENTER, bold=True, leading=26)),
            ],
            [
                Paragraph('kg CO₂e per year', _s('HL1', size=8, color=C['muted'], align=TA_CENTER)),
                Paragraph('Carbon Level', _s('HL2', size=8, color=C['muted'], align=TA_CENTER)),
                Paragraph('Assessment Year', _s('HL3', size=8, color=C['muted'], align=TA_CENTER)),
            ],
        ]
        hero_table = Table(hero_data, colWidths=[W/3]*3)
        hero_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), C['sage']),
            ('BACKGROUND', (0,0), (0,-1), colors.HexColor('#f0fff4')),
            ('BOX', (0,0), (-1,-1), 1, C['sage2']),
            ('LINEAFTER', (0,0), (1,-1), 0.5, C['gray2']),
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('TOPPADDING', (0,0), (-1,-1), 16),
            ('BOTTOMPADDING', (0,0), (-1,-1), 16),
            ('ROUNDEDCORNERS', [12, 12, 12, 12]),
        ]))
        story.append(hero_table)
        story.append(Spacer(1, 24))

        # ── PROFILE SUMMARY ───────────────────────────────────────────────────
        story.append(Paragraph('Assessment Overview', sSec))
        story.append(GradientBar(W, 3, C['primary'], C['emerald']))
        story.append(Spacer(1, 12))

        profile_rows = [
            [Paragraph('Field', sTH), Paragraph('Your Data', sTH), Paragraph('Field', sTH), Paragraph('Your Data', sTH)],
        ]
        fields = [
            ('Country',           assessment_data.get('country', '—')),
            ('Electricity',        f"{assessment_data.get('electricity_kwh', '—')} kWh/month"),
            ('Vehicle Type',      assessment_data.get('vehicle_type', '—').title()),
            ('Vehicle Distance',   f"{assessment_data.get('vehicle_km', '—')} km/month"),
            ('Flight Type',       assessment_data.get('flight_type', '—').title()),
            ('Diet Type',         assessment_data.get('diet_type', '—').title()),
            ('Shopping',          assessment_data.get('shopping_freq', '—').title()),
            ('Recycling',         assessment_data.get('recycling', '—').title()),
        ]
        # Build 2-column layout
        for i in range(0, len(fields), 2):
            row = []
            for j in [i, i+1]:
                if j < len(fields):
                    row.append(Paragraph(fields[j][0], _s(f'PK{j}', size=8, color=C['muted'], bold=True)))
                    row.append(Paragraph(str(fields[j][1]), _s(f'PV{j}', size=9, color=C['black'])))
                else:
                    row += [Paragraph('', sTD), Paragraph('', sTD)]
            profile_rows.append(row)

        profile_table = Table(profile_rows, colWidths=[W*0.22, W*0.28, W*0.22, W*0.28])
        profile_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), C['primary']),
            ('TEXTCOLOR',  (0,0), (-1,0), colors.white),
            ('FONTNAME',   (0,0), (-1,0), FONT_BOLD),
            ('FONTSIZE',   (0,0), (-1,0), 9),
            ('ALIGN',      (0,0), (-1,-1), 'CENTER'),
            ('VALIGN',     (0,0), (-1,-1), 'MIDDLE'),
            ('GRID',       (0,0), (-1,-1), 0.5, C['gray2']),
            ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, C['gray1']]),
            ('TOPPADDING',    (0,0), (-1,-1), 8),
            ('BOTTOMPADDING', (0,0), (-1,-1), 8),
            ('LEFTPADDING',   (0,0), (-1,-1), 10),
        ]))
        story.append(profile_table)
        story.append(Spacer(1, 24))

        # ── EMISSIONS BREAKDOWN ───────────────────────────────────────────────
        story.append(Paragraph('Emissions Breakdown', sSec))
        story.append(GradientBar(W, 3, C['primary'], C['emerald']))
        story.append(Spacer(1, 12))

        breakdown = assessment_data.get('breakdown', {})
        if breakdown:
            bk_data = [
                [Paragraph(h, sTH) for h in ['Category', 'kg CO₂e / year', '% of Total']],
            ]
            total_calc = sum(breakdown.values()) or 1
            for name, val in breakdown.items():
                pct = val / total_calc * 100
                row = [
                    Paragraph(f'<b>{name.replace("_", " ").title()}</b>', sTDL),
                    Paragraph(f'{int(val):,}', _s(f'BV{name}', size=9, color=C['primary'], align=TA_CENTER, bold=True)),
                    Paragraph(f'{pct:.1f}%', _s(f'BP{name}', size=9, color=C['muted'], align=TA_CENTER)),
                ]
                bk_data.append(row)

            bk_table = Table(bk_data, colWidths=[W*0.4, W*0.3, W*0.3])
            bk_table.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,0), C['forest']),
                ('TEXTCOLOR',  (0,0), (-1,0), colors.white),
                ('GRID',       (0,0), (-1,-1), 0.5, C['gray2']),
                ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, C['gray1']]),
                ('VALIGN',     (0,0), (-1,-1), 'MIDDLE'),
                ('TOPPADDING',    (0,0), (-1,-1), 9),
                ('BOTTOMPADDING', (0,0), (-1,-1), 9),
                ('LEFTPADDING',   (0,0), (-1,-1), 10),
            ]))
            story.append(bk_table)
            story.append(Spacer(1, 24))

        # ── BENCHMARK ─────────────────────────────────────────────────────────
        story.append(Paragraph('Benchmarking', sSec))
        story.append(GradientBar(W, 3, C['primary'], C['emerald']))
        story.append(Spacer(1, 12))

        benchmarks = [
            ('Your Footprint',      footprint,  level_color,    True),
            ('Global Average',      7_200,      C['warning'],   False),
            ('Sustainable Target',  2_000,      C['emerald'],   False),
            ('India Average',       1_900,      C['muted'],     False),
            ('USA Average',         16_000,     C['danger'],    False),
            ('EU Average',          7_000,      C['sky'],       False),
        ]
        max_val = max(v for _, v, _, _ in benchmarks) or 1

        bm_data = [[Paragraph(h, sTH) for h in ['Entity', 'kg CO₂e / yr']]]
        for name, val, col, bold in benchmarks:
            bm_data.append([
                Paragraph(f'<b>{name}</b>' if bold else name, _s(f'BMN{name}', size=9, color=col, align=TA_CENTER, bold=bold)),
                Paragraph(f'{int(val):,}', _s(f'BMV{name}', size=9, color=col, align=TA_CENTER, bold=bold)),
            ])

        bm_table = Table(bm_data, colWidths=[W*0.7, W*0.3])
        bm_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), C['forest']),
            ('TEXTCOLOR',  (0,0), (-1,0), colors.white),
            ('BACKGROUND', (0,1), (-1,1), colors.HexColor('#f0fff4')),
            ('GRID',       (0,0), (-1,-1), 0.5, C['gray2']),
            ('ROWBACKGROUNDS', (0,2), (-1,-1), [colors.white, C['gray1']]),
            ('VALIGN',     (0,0), (-1,-1), 'MIDDLE'),
            ('TOPPADDING',    (0,0), (-1,-1), 9),
            ('BOTTOMPADDING', (0,0), (-1,-1), 9),
            ('LEFTPADDING',   (0,0), (-1,-1), 10),
        ]))
        story.append(bm_table)
        story.append(Spacer(1, 24))

        # ── RECOMMENDATIONS ───────────────────────────────────────────────────
        story.append(Paragraph('Personalised Recommendations', sSec))
        story.append(GradientBar(W, 3, C['primary'], C['emerald']))
        story.append(Spacer(1, 12))

        if recommendations:
            rec_data = [[Paragraph(h, sTH) for h in ['#', 'Recommendation']]]
            for i, rec in enumerate(recommendations[:8], 1):
                if isinstance(rec, dict):
                    text = rec.get('text', str(rec))
                else:
                    text = str(rec)
                rec_data.append([
                    Paragraph(f'<b>{i}</b>', _s(f'RN{i}', size=10, color=C['primary'], align=TA_CENTER, bold=True)),
                    Paragraph(text, sRec),
                ])
            rec_table = Table(rec_data, colWidths=[W*0.1, W*0.9])
            rec_table.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,0), C['primary']),
                ('TEXTCOLOR',  (0,0), (-1,0), colors.white),
                ('GRID',       (0,0), (-1,-1), 0.5, C['gray2']),
                ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, C['sage']]),
                ('VALIGN',     (0,0), (-1,-1), 'MIDDLE'),
                ('TOPPADDING',    (0,0), (-1,-1), 9),
                ('BOTTOMPADDING', (0,0), (-1,-1), 9),
                ('LEFTPADDING',   (0,1), (-1,-1), 12),
            ]))
            story.append(rec_table)
        else:
            story.append(Paragraph(
                'Continue monitoring your footprint regularly and aim to reduce consumption in your highest-impact categories.',
                sBody
            ))

        story.append(Spacer(1, 28))

        # ── DISCLAIMER ────────────────────────────────────────────────────────
        story.append(SectionDivider(W))
        story.append(Spacer(1, 12))
        disc = (
            'This carbon footprint report is generated by the Carbon ESG Platform for educational '
            'and awareness purposes only. Figures are AI-estimated based on provided inputs and standard '
            'emission factors (DEFRA). They do not constitute formal environmental certification or regulatory '
            'compliance documentation. For official carbon accounting, please engage a qualified sustainability consultant.'
        )
        story.append(Paragraph(disc, _s('Disc', size=7.5, color=C['muted'], align=TA_JUSTIFY, leading=12)))

        doc.build(story, onFirstPage=_header_footer_carbon, onLaterPages=_header_footer_carbon)
        return filename

    # ── ESG Report ────────────────────────────────────────────────────────────

    def generate_enterprise_report(self, user_data: dict, assessment_data: dict, recommendations=None) -> str:
        """
        Generate a beautiful, professional ESG Readiness Report.
        """
        if recommendations is None:
            recommendations = assessment_data.get('recommendations', [])
        
        # Convert to list if it's not already a list
        if not isinstance(recommendations, list):
            if isinstance(recommendations, dict):
                recommendations = list(recommendations.values())
            else:
                recommendations = []
            
        filename = f"esg_report_{user_data['username']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        filepath = os.path.join('static', 'reports', filename)
        os.makedirs(os.path.dirname(filepath), exist_ok=True)

        doc = SimpleDocTemplate(
            filepath, pagesize=A4,
            rightMargin=36, leftMargin=36,
            topMargin=60, bottomMargin=48,
            title='ESG Readiness Report',
            author='Carbon ESG Platform',
        )

        story = []
        W = A4[0] - 72

        sTitle = _s('ET', size=24, color=C['navy'], align=TA_CENTER, bold=True, leading=30, after=4)
        sSub   = _s('ES', size=11, color=C['blue'],  align=TA_CENTER, leading=15, after=20)
        sSec   = _s('ESecH', size=13, color=C['navy'], bold=True, before=6, after=10)
        sBody  = _s('EBody', size=10, color=C['text'], leading=15, after=8)
        sTH    = _s('ETH', size=9, color=colors.white, align=TA_CENTER, bold=True)
        sTD    = _s('ETD', size=9, color=C['text'], align=TA_CENTER, leading=13)
        sTDL   = _s('ETDL', size=9, color=C['text'], leading=13)

        esg_score   = assessment_data.get('total_score', 0)
        esg_risk    = assessment_data.get('esg_risk', 'Medium')
        company     = assessment_data.get('company_name', user_data.get('username', 'Company'))
        industry    = assessment_data.get('industry', '—').title()
        env_score   = assessment_data.get('environmental_score', esg_score * 0.7)
        soc_score   = assessment_data.get('social_score', esg_score * 0.15)
        gov_score   = assessment_data.get('governance_score', esg_score * 0.15)

        risk_color = C['emerald'] if esg_risk == 'Low' else C['warning'] if esg_risk == 'Medium' else C['danger']

        # ── COVER ─────────────────────────────────────────────────────────────
        story.append(Spacer(1, 10))
        story.append(GradientBar(W, 6, C['navy'], C['sky']))
        story.append(Spacer(1, 24))

        story.append(Paragraph('ESG Readiness Report', sTitle))
        story.append(Paragraph(f'{company}  ·  {industry}  ·  {datetime.now().strftime("%B %Y")}', sSub))

        # ESG Score hero
        hero_data = [
            [
                Paragraph(f'<b>{esg_score}</b>', _s('SV', size=30, color=C['navy'], align=TA_CENTER, bold=True, leading=34)),
                Paragraph(f'<b>{esg_risk} Risk</b>', _s('RV', size=18, color=risk_color, align=TA_CENTER, bold=True, leading=22)),
                Paragraph(f'<b>{int(env_score)}</b>', _s('EV', size=20, color=C['primary'], align=TA_CENTER, bold=True, leading=24)),
                Paragraph(f'<b>{int(soc_score)}</b>', _s('SoV', size=20, color=C['blue'], align=TA_CENTER, bold=True, leading=24)),
                Paragraph(f'<b>{int(gov_score)}</b>', _s('GV', size=20, color=colors.HexColor('#4527a0'), align=TA_CENTER, bold=True, leading=24)),
            ],
            [
                Paragraph('Overall Score / 100', _s('SL', size=8, color=C['muted'], align=TA_CENTER)),
                Paragraph('Risk Classification', _s('RL', size=8, color=C['muted'], align=TA_CENTER)),
                Paragraph('Environmental', _s('EL', size=8, color=C['muted'], align=TA_CENTER)),
                Paragraph('Social', _s('SoL', size=8, color=C['muted'], align=TA_CENTER)),
                Paragraph('Governance', _s('GL', size=8, color=C['muted'], align=TA_CENTER)),
            ],
        ]
        hero_table = Table(hero_data, colWidths=[W/5]*5)
        hero_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#f0f6ff')),
            ('BACKGROUND', (0,0), (0,-1), colors.HexColor('#e8f0fe')),
            ('BOX', (0,0), (-1,-1), 1, colors.HexColor('#c5d5f5')),
            ('LINEAFTER', (0,0), (3,-1), 0.5, colors.HexColor('#c5d5f5')),
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('TOPPADDING', (0,0), (-1,-1), 16),
            ('BOTTOMPADDING', (0,0), (-1,-1), 16),
        ]))
        story.append(hero_table)
        story.append(Spacer(1, 24))

        # ── COMPANY PROFILE ────────────────────────────────────────────────────
        story.append(Paragraph('Company Profile', sSec))
        story.append(GradientBar(W, 3, C['navy'], C['sky']))
        story.append(Spacer(1, 12))

        co_fields = [
            ('Company Name',     company),
            ('Industry',         industry),
            ('Employees',        f"{assessment_data.get('employees', 0):,}"),
            ('Energy Usage',     f"{int(assessment_data.get('energy_usage', 0)):,} kWh/mo"),
            ('Business Travel',  f"{int(assessment_data.get('travel_km', 0)):,} km/yr"),
            ('Cloud Usage',      assessment_data.get('cloud_usage', '—').title()),
            ('Waste Management', f"Level {assessment_data.get('waste_management', '—')} / 5"),
        ]
        co_rows = [[Paragraph(h, sTH) for h in ['Field', 'Value']]]
        for i in range(0, len(co_fields)):
            row = [
                Paragraph(co_fields[i][0], _s(f'CF{i}', size=8, color=C['muted'], bold=True)),
                Paragraph(str(co_fields[i][1]), _s(f'CV{i}', size=9, color=C['black'])),
            ]
            co_rows.append(row)

        co_table = Table(co_rows, colWidths=[W*0.3, W*0.7])
        co_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), C['navy']),
            ('TEXTCOLOR',  (0,0), (-1,0), colors.white),
            ('GRID',       (0,0), (-1,-1), 0.5, C['gray2']),
            ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor('#f0f6ff')]),
            ('VALIGN',     (0,0), (-1,-1), 'MIDDLE'),
            ('TOPPADDING', (0,0), (-1,-1), 8),
            ('BOTTOMPADDING', (0,0), (-1,-1), 8),
            ('LEFTPADDING', (0,0), (-1,-1), 10),
        ]))
        story.append(co_table)
        story.append(Spacer(1, 24))

        # ── ESG PILLAR SCORES ─────────────────────────────────────────────────
        story.append(Paragraph('ESG Pillar Analysis', sSec))
        story.append(GradientBar(W, 3, C['navy'], C['sky']))
        story.append(Spacer(1, 12))

        def score_band(s):
            if s >= 75: return ('Excellent', C['emerald'])
            if s >= 55: return ('Good',      C['primary'])
            if s >= 35: return ('Fair',      C['warning'])
            return ('Poor', C['danger'])

        pillars = [
            ('Environmental', env_score, 70, C['primary']),
            ('Social', soc_score, 15, C['blue']),
            ('Governance', gov_score, 15, colors.HexColor('#4527a0')),
        ]

        pillar_data = [[Paragraph(h, sTH) for h in ['Pillar', 'Score', 'Weight', 'Band']]]
        for name, score, weight, col in pillars:
            band, band_col = score_band(score)
            pillar_data.append([
                Paragraph(f'<b>{name}</b>', _s(f'PN{name}', size=9, color=col, bold=True)),
                Paragraph(f'<b>{int(score)}</b>', _s(f'PS{name}', size=9, color=col, align=TA_CENTER, bold=True)),
                Paragraph(f'{weight}%', _s(f'PW{name}', size=9, color=C['muted'], align=TA_CENTER)),
                Paragraph(band, _s(f'PB{name}', size=9, color=band_col, align=TA_CENTER, bold=True)),
            ])

        pillar_table = Table(pillar_data, colWidths=[W*0.3, W*0.2, W*0.2, W*0.3])
        pillar_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), C['navy']),
            ('TEXTCOLOR',  (0,0), (-1,0), colors.white),
            ('GRID',       (0,0), (-1,-1), 0.5, C['gray2']),
            ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor('#f0f6ff')]),
            ('VALIGN',     (0,0), (-1,-1), 'MIDDLE'),
            ('TOPPADDING',    (0,0), (-1,-1), 10),
            ('BOTTOMPADDING', (0,0), (-1,-1), 10),
            ('LEFTPADDING',   (0,0), (-1,-1), 10),
        ]))
        story.append(pillar_table)
        story.append(Spacer(1, 24))

        # ── KEY METRICS ────────────────────────────────────────────────────
        story.append(Paragraph('Key Performance Metrics', sSec))
        story.append(GradientBar(W, 3, C['navy'], C['sky']))
        story.append(Spacer(1, 12))

        metrics_data = [
            ['Emissions per Employee', f"{assessment_data.get('emissions_per_employee', 0)} tons CO2e"],
            ['Energy Intensity', f"{assessment_data.get('energy_intensity', 0)} kWh/employee"],
        ]
        metrics_table = Table(metrics_data, colWidths=[W*0.5, W*0.5])
        metrics_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#f0f6ff')),
            ('GRID', (0,0), (-1,-1), 0.5, C['gray2']),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('TOPPADDING', (0,0), (-1,-1), 10),
            ('BOTTOMPADDING', (0,0), (-1,-1), 10),
            ('LEFTPADDING', (0,0), (-1,-1), 10),
        ]))
        story.append(metrics_table)
        story.append(Spacer(1, 24))

        # ── RECOMMENDATIONS ────────────────────────────────────────────────────
        if recommendations:
            story.append(Paragraph('Strategic Recommendations', sSec))
            story.append(GradientBar(W, 3, C['navy'], C['sky']))
            story.append(Spacer(1, 12))

            rec_data = [[Paragraph(h, sTH) for h in ['Recommendation']]]
            for i, rec in enumerate(recommendations[:6], 1):
                if isinstance(rec, dict):
                    txt = rec.get('text', str(rec))
                else:
                    txt = str(rec)
                rec_data.append([Paragraph(f'{i}. {txt}', _s(f'RT{i}', size=9, leading=13))])

            rec_table = Table(rec_data, colWidths=[W])
            rec_table.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,0), C['navy']),
                ('TEXTCOLOR',  (0,0), (-1,0), colors.white),
                ('GRID',       (0,0), (-1,-1), 0.5, C['gray2']),
                ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor('#f0f6ff')]),
                ('VALIGN',     (0,0), (-1,-1), 'MIDDLE'),
                ('TOPPADDING',    (0,0), (-1,-1), 9),
                ('BOTTOMPADDING', (0,0), (-1,-1), 9),
                ('LEFTPADDING',   (0,1), (-1,-1), 20),
            ]))
            story.append(rec_table)
            story.append(Spacer(1, 24))

        # ── DISCLAIMER ────────────────────────────────────────────────────────
        story.append(SectionDivider(W, color=colors.HexColor('#c5d5f5')))
        story.append(Spacer(1, 12))
        story.append(Paragraph(
            'This ESG readiness report is generated by the Carbon ESG Platform for educational and strategic awareness '
            'purposes only. It does not constitute formal ESG certification, audit, regulatory compliance documentation, '
            'or investment advice. For formal ESG reporting and certification, engage qualified sustainability consultants '
            'and follow established frameworks (GRI, SASB, TCFD, ISSB).',
            _s('EDisc', size=7.5, color=C['muted'], align=TA_JUSTIFY, leading=12)
        ))

        doc.build(story, onFirstPage=_header_footer_esg, onLaterPages=_header_footer_esg)
        return filename

    # ── Certificate ───────────────────────────────────────────────────────────

    def generate_certificate(self, user_data: dict, assessment_type: str, score) -> str:
        """
        Generate a beautiful, elegant participation certificate.
        Landscape A4 with gold border, seal, and premium typography.
        """
        filename = f"certificate_{user_data['username']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        filepath = os.path.join('static', 'reports', filename)
        os.makedirs(os.path.dirname(filepath), exist_ok=True)

        # Landscape A4
        page_w, page_h = landscape(A4)

        doc = SimpleDocTemplate(
            filepath,
            pagesize=landscape(A4),
            rightMargin=60, leftMargin=60,
            topMargin=60, bottomMargin=60,
            title='Certificate of Achievement',
            author='Carbon ESG Platform',
        )

        def cert_background(canvas, doc):
            """Draw the full certificate background and border."""
            canvas.saveState()

            # Cream parchment background
            canvas.setFillColor(C['cream'])
            canvas.rect(0, 0, page_w, page_h, stroke=0, fill=1)

            # Subtle texture (thin horizontal lines)
            canvas.setStrokeColor(colors.HexColor('#f0e8d0'))
            canvas.setLineWidth(0.3)
            for y in range(0, int(page_h), 6):
                canvas.line(0, y, page_w, y)

            # Outer gold border
            canvas.setStrokeColor(C['amber'])
            canvas.setLineWidth(3)
            canvas.roundRect(20, 20, page_w - 40, page_h - 40, 8, stroke=1, fill=0)

            # Inner thin gold border
            canvas.setStrokeColor(C['gold2'])
            canvas.setLineWidth(0.8)
            canvas.roundRect(28, 28, page_w - 56, page_h - 56, 5, stroke=1, fill=0)

            # Corner ornaments
            for x, y, ang in [
                (20, page_h - 20, 0),
                (page_w - 20, page_h - 20, 90),
                (page_w - 20, 20, 180),
                (20, 20, 270),
            ]:
                canvas.saveState()
                canvas.translate(x, y)
                canvas.rotate(ang)
                canvas.setFillColor(C['amber'])
                canvas.rect(0, 0, 18, 18, stroke=0, fill=1)
                canvas.setFillColor(C['gold2'])
                canvas.rect(3, 3, 12, 12, stroke=0, fill=1)
                canvas.restoreState()

            # Top decorative green strip
            canvas.setFillColor(C['primary'])
            canvas.rect(40, page_h - 48, page_w - 80, 12, stroke=0, fill=1)

            # Gradient over the strip
            steps = 40
            sw = (page_w - 80) / steps
            for i in range(steps):
                t = i / steps
                r = C['primary'].red + (C['emerald'].red - C['primary'].red) * t
                g = C['primary'].green + (C['emerald'].green - C['primary'].green) * t
                b = C['primary'].blue + (C['emerald'].blue - C['primary'].blue) * t
                canvas.setFillColor(colors.Color(r, g, b))
                canvas.rect(40 + i * sw, page_h - 48, sw + 1, 12, stroke=0, fill=1)

            # Bottom strip (mirror)
            canvas.setFillColor(C['primary'])
            canvas.rect(40, 36, page_w - 80, 12, stroke=0, fill=1)
            for i in range(steps):
                t = i / steps
                r = C['primary'].red + (C['emerald'].red - C['primary'].red) * t
                g = C['primary'].green + (C['emerald'].green - C['primary'].green) * t
                b = C['primary'].blue + (C['emerald'].blue - C['primary'].blue) * t
                canvas.setFillColor(colors.Color(r, g, b))
                canvas.rect(40 + i * sw, 36, sw + 1, 12, stroke=0, fill=1)

            # Gold Seal (bottom-right)
            sx, sy, sr = page_w - 100, 60, 38
            # Outer
            canvas.setFillColor(C['gold2'])
            canvas.setStrokeColor(C['amber'])
            canvas.setLineWidth(2)
            canvas.circle(sx, sy, sr, stroke=1, fill=1)
            # Inner ring
            canvas.setFillColor(colors.HexColor('#ffeaa0'))
            canvas.setStrokeColor(C['amber'])
            canvas.setLineWidth(1)
            canvas.circle(sx, sy, sr - 8, stroke=1, fill=1)
            # Star
            canvas.setFillColor(C['amber'])
            canvas.setFont(FONT_BOLD, 22)
            canvas.drawCentredString(sx, sy - 8, '★')

            # Platform watermark (faint, diagonal)
            canvas.saveState()
            canvas.setFillColor(colors.HexColor('#e8dfc8'))
            canvas.setFont(FONT_LIGHT, 52)
            canvas.translate(page_w / 2, page_h / 2)
            canvas.rotate(25)
            canvas.drawCentredString(0, 0, 'Carbon·ESG')
            canvas.restoreState()

            canvas.restoreState()

        story = []
        W = page_w - 120

        # ── CERT CONTENT ──────────────────────────────────────────────────────
        story.append(Spacer(1, 18))

        # Platform name
        story.append(Paragraph(
            'Carbon<font color="#2ecc71">.</font>ESG Platform',
            _s('CPN', size=13, color=C['mid'], align=TA_CENTER, bold=True, after=4)
        ))

        story.append(Spacer(1, 8))

        # Main certificate title
        story.append(Paragraph(
            'CERTIFICATE OF ACHIEVEMENT',
            _s('CTit', size=28, color=C['forest'], align=TA_CENTER, bold=True, leading=34, after=4)
        ))

        story.append(Spacer(1, 6))

        # "This is to certify"
        story.append(Paragraph(
            'This is to certify that',
            _s('CTC', size=13, color=C['muted'], align=TA_CENTER, after=4, font=FONT_LIGHT)
        ))

        # Recipient name (large, elegant)
        username = user_data.get('username', 'Participant')
        story.append(Paragraph(
            username,
            _s('CName', size=34, color=C['forest'], align=TA_CENTER, bold=True, leading=40, after=8)
        ))

        story.append(Spacer(1, 14))

        story.append(Paragraph(
            'has successfully completed the',
            _s('CTC2', size=13, color=C['muted'], align=TA_CENTER, after=6, font=FONT_LIGHT)
        ))

        story.append(Paragraph(
            assessment_type,
            _s('CType', size=16, color=C['primary'], align=TA_CENTER, bold=True, after=4)
        ))

        story.append(Paragraph(
            'on the Carbon ESG Platform',
            _s('CTC3', size=11, color=C['muted'], align=TA_CENTER, after=16, font=FONT_LIGHT)
        ))

        # Score and date row
        meta_data = [
            [
                Paragraph(f'<b>{score}</b>', _s('CMScore', size=22, color=C['amber'], align=TA_CENTER, bold=True, leading=26)),
                Paragraph(f'<b>{datetime.now().strftime("%d %B %Y")}</b>', _s('CMDate', size=14, color=C['forest'], align=TA_CENTER, bold=True, leading=18)),
            ],
            [
                Paragraph('Assessment Score', _s('CMSLbl', size=8, color=C['muted'], align=TA_CENTER)),
                Paragraph('Date of Issue', _s('CMLbl', size=8, color=C['muted'], align=TA_CENTER)),
            ],
        ]
        meta_table = Table(meta_data, colWidths=[W*0.4, W*0.6])
        meta_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#f9f4e4')),
            ('BOX',        (0,0), (-1,-1), 1, C['amber']),
            ('LINEAFTER',  (0,0), (0,-1), 0.5, C['amber']),
            ('ALIGN',      (0,0), (-1,-1), 'CENTER'),
            ('VALIGN',     (0,0), (-1,-1), 'MIDDLE'),
            ('TOPPADDING', (0,0), (-1,-1), 12),
            ('BOTTOMPADDING', (0,0), (-1,-1), 12),
            ('ROUNDEDCORNERS', [6, 6, 6, 6]),
        ]))
        story.append(meta_table)
        story.append(Spacer(1, 20))

        # Signature row
        sig_data = [
            [
                Paragraph('_' * 28, _s('SigAL', size=10, color=C['primary'], align=TA_CENTER)),
                Paragraph('_' * 28, _s('SigBL', size=10, color=C['primary'], align=TA_CENTER)),
            ],
            [
                Paragraph('Authorised Signatory', _s('SigAN', size=8, color=C['muted'], align=TA_CENTER)),
                Paragraph('Carbon ESG Platform', _s('SigBN', size=8, color=C['muted'], align=TA_CENTER)),
            ],
        ]
        sig_table = Table(sig_data, colWidths=[W*0.5, W*0.5])
        sig_table.setStyle(TableStyle([
            ('ALIGN',  (0,0), (-1,-1), 'CENTER'),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('TOPPADDING', (0,0), (-1,-1), 4),
            ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ]))
        story.append(sig_table)
        story.append(Spacer(1, 16))

        # Disclaimer
        story.append(Paragraph(
            'This certificate is issued for educational participation purposes only. '
            'It does not constitute formal professional certification or regulatory compliance documentation.',
            _s('CDi', size=7.5, color=C['gray3'], align=TA_CENTER, leading=11)
        ))

        doc.build(story, onFirstPage=cert_background, onLaterPages=cert_background)
        return filename