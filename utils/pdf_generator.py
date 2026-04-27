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
import io
import os
import math

BASE_DIR = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))

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

# ── Brand Colours (Tailwind Matched) ───────────────────────────────────────────
C = {
    # Tailwind Green/Emerald Theme
    'brand950':  colors.HexColor('#052e16'),
    'brand900':  colors.HexColor('#14532d'),
    'brand800':  colors.HexColor('#166534'),
    'brand700':  colors.HexColor('#15803d'),
    'brand600':  colors.HexColor('#16a34a'),
    'brand500':  colors.HexColor('#22c55e'),
    'brand400':  colors.HexColor('#4ade80'),
    'brand100':  colors.HexColor('#dcfce7'),
    'brand50':   colors.HexColor('#f0fdf4'),

    # Tailwind Blue Theme
    'blue900':   colors.HexColor('#1e3a8a'),
    'blue800':   colors.HexColor('#1e40af'),
    'blue600':   colors.HexColor('#2563eb'),
    'blue500':   colors.HexColor('#3b82f6'),
    'blue50':    colors.HexColor('#eff6ff'),

    # Tailwind Grays
    'gray900':   colors.HexColor('#111827'),
    'gray800':   colors.HexColor('#1f2937'),
    'gray600':   colors.HexColor('#4b5563'),
    'gray500':   colors.HexColor('#6b7280'),
    'gray400':   colors.HexColor('#9ca3af'),
    'gray200':   colors.HexColor('#e5e7eb'),
    'gray50':    colors.HexColor('#f9fafb'),

    # Status Colors
    'yellow500': colors.HexColor('#eab308'),
    'yellow50':  colors.HexColor('#fefce8'),
    'red500':    colors.HexColor('#ef4444'),
    'red50':     colors.HexColor('#fef2f2'),
    'white':     colors.white,
}

# Aliases for backward compatibility in the code
C['forest']    = C['brand950']
C['primary']   = C['brand600']
C['mid']       = C['brand700']
C['emerald']   = C['brand500']
C['sage']      = C['brand50']
C['sage2']     = C['brand100']
C['navy']      = C['blue900']
C['blue']      = C['blue600']
C['sky']       = C['blue500']
C['amber']     = C['yellow500']
C['gold2']     = C['yellow500']
C['cream']     = C['yellow50']
C['warning']   = C['yellow500']
C['danger']    = C['red500']
C['black']     = C['gray900']
C['text']      = C['gray800']
C['muted']     = C['gray500']
C['gray1']     = C['gray50']
C['gray2']     = C['gray200']
C['gray3']     = C['gray500']


# ── Custom Flowables ───────────────────────────────────────────────────────────

class GradientBar(Flowable):
    """Horizontal gradient bar — used as section dividers."""
    def __init__(self, width, height=4, c1=None, c2=None):
        Flowable.__init__(self)
        self.width  = width
        self.height = height
        self.c1 = c1 or C['brand800']
        self.c2 = c2 or C['brand400']

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
    """Thin elegant divider."""
    def __init__(self, width, color=None):
        Flowable.__init__(self)
        self.width = width
        self.color = color or C['gray2']

    def draw(self):
        self.canv.setStrokeColor(self.color)
        self.canv.setLineWidth(1)
        self.canv.line(0, 2, self.width, 2)


# ── Page Callbacks ─────────────────────────────────────────────────────────────

def _header_footer_carbon(canvas, doc):
    """Carbon report header/footer drawn on every page."""
    canvas.saveState()
    w, h = A4

    # Top bar
    canvas.setFillColor(C['brand950'])
    canvas.rect(0, h - 44, w, 44, stroke=0, fill=1)

    # Brand name
    canvas.setFillColor(colors.white)
    canvas.setFont(FONT_BOLD, 12)
    canvas.drawString(36, h - 28, 'Carbon.ESG')

    canvas.setFillColor(C['brand400'])
    canvas.setFont(FONT_REGULAR, 9)
    canvas.drawRightString(w - 36, h - 28, 'Carbon Footprint Report  |  Confidential')

    # Bottom bar
    canvas.setFillColor(C['gray50'])
    canvas.rect(0, 0, w, 36, stroke=0, fill=1)

    canvas.setFillColor(C['gray500'])
    canvas.setFont(FONT_REGULAR, 8)
    canvas.drawString(36, 14, f'Generated: {datetime.now().strftime("%d %B %Y, %H:%M")}')
    canvas.drawRightString(w - 36, 14, f'Page {doc.page}  |  Carbon ESG Platform')

    # Thin gradient top accent
    steps = 30
    bw = w / steps
    for i in range(steps):
        t = i / steps
        r = C['brand600'].red + (C['brand400'].red - C['brand600'].red) * t
        g = C['brand600'].green + (C['brand400'].green - C['brand600'].green) * t
        b = C['brand600'].blue + (C['brand400'].blue - C['brand600'].blue) * t
        canvas.setFillColor(colors.Color(r, g, b))
        canvas.rect(i * bw, h - 48, bw + 1, 4, stroke=0, fill=1)

    canvas.restoreState()


def _header_footer_esg(canvas, doc):
    """ESG report header/footer."""
    canvas.saveState()
    w, h = A4

    canvas.setFillColor(C['blue900'])
    canvas.rect(0, h - 44, w, 44, stroke=0, fill=1)

    canvas.setFillColor(colors.white)
    canvas.setFont(FONT_BOLD, 12)
    canvas.drawString(36, h - 28, 'Carbon.ESG')

    canvas.setFillColor(C['blue500'])
    canvas.setFont(FONT_REGULAR, 9)
    canvas.drawRightString(w - 36, h - 28, 'ESG Readiness Report  |  Confidential')

    canvas.setFillColor(C['blue50'])
    canvas.rect(0, 0, w, 36, stroke=0, fill=1)

    canvas.setFillColor(C['gray600'])
    canvas.setFont(FONT_REGULAR, 8)
    canvas.drawString(36, 14, f'Generated: {datetime.now().strftime("%d %B %Y, %H:%M")}')
    canvas.drawRightString(w - 36, 14, f'Page {doc.page}  |  Carbon ESG Platform')

    steps = 30
    bw = w / steps
    for i in range(steps):
        t = i / steps
        r = C['blue800'].red + (C['blue500'].red - C['blue800'].red) * t
        g = C['blue800'].green + (C['blue500'].green - C['blue800'].green) * t
        b = C['blue800'].blue + (C['blue500'].blue - C['blue800'].blue) * t
        canvas.setFillColor(colors.Color(r, g, b))
        canvas.rect(i * bw, h - 48, bw + 1, 4, stroke=0, fill=1)

    canvas.restoreState()


# ── Helper: build paragraph style dict ────────────────────────────────────────

def _s(name, base='Normal', font=None, size=10, color=None, align=TA_LEFT,
       leading=None, before=0, after=8, bold=False):
    """Create a paragraph style"""
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
        
        if not isinstance(recommendations, list):
            if isinstance(recommendations, dict):
                recommendations = list(recommendations.values())
            else:
                recommendations = []
            
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer, pagesize=A4,
            rightMargin=36, leftMargin=36,
            topMargin=60, bottomMargin=48,
            title='Carbon Footprint Report',
            author='Carbon ESG Platform',
        )

        story = []
        W = A4[0] - 72   # usable width

        # ── STYLES ────────────────────────────────────────────────────────────
        sTitle    = _s('Title',    size=28, color=C['gray900'], align=TA_CENTER, bold=True, leading=34, after=4)
        sSub      = _s('Sub',      size=12, color=C['gray500'], align=TA_CENTER, leading=16, after=24)
        sSec      = _s('Sec',      size=16, color=C['gray900'], bold=True, before=10, after=8)
        sBody     = _s('Body',     size=10, color=C['gray800'], leading=16, after=8)
        sRec      = _s('Rec',      size=10, color=C['gray800'], leading=15, after=6)
        sTH       = _s('TH',       size=9,  color=C['gray500'], align=TA_LEFT, bold=True)
        sTD       = _s('TD',       size=10, color=C['gray900'], align=TA_LEFT, leading=14)

        footprint = assessment_data.get('total_footprint', 0)
        level     = assessment_data.get('carbon_level', 'Medium')
        username  = user_data.get('username', 'User')

        level_color = C['brand500'] if level == 'Low' else C['warning'] if level == 'Medium' else C['danger']

        # ── COVER BLOCK ───────────────────────────────────────────────────────
        story.append(Spacer(1, 10))
        story.append(Paragraph('Carbon Footprint Report', sTitle))
        story.append(Paragraph(f'Personalized Assessment for <b>{username}</b>', sSub))

        # Hero metric table (Rounded Card)
        hero_data = [
            [
                Paragraph(f'<b>{int(footprint):,}</b>', _s('H1', size=32, color=level_color, align=TA_CENTER, bold=True, leading=36)),
                Paragraph(f'<b>{level}</b>', _s('H2', size=24, color=level_color, align=TA_CENTER, bold=True, leading=28)),
            ],
            [
                Paragraph('kg CO₂e / Year', _s('HL1', size=9, color=C['gray500'], align=TA_CENTER)),
                Paragraph('Impact Level', _s('HL2', size=9, color=C['gray500'], align=TA_CENTER)),
            ],
        ]
        hero_table = Table(hero_data, colWidths=[W/2]*2)
        hero_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), C['brand50']),
            ('LINEBETWEEN', (0,0), (-1,-1), 1, C['brand100']),
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('TOPPADDING', (0,0), (-1,-1), 20),
            ('BOTTOMPADDING', (0,0), (-1,-1), 20),
            ('ROUNDEDCORNERS', [16, 16, 16, 16]),
        ]))
        story.append(hero_table)
        story.append(Spacer(1, 30))

        # ── PROFILE SUMMARY ───────────────────────────────────────────────────
        story.append(Paragraph('Input Summary', sSec))
        story.append(GradientBar(W, 2, C['brand500'], C['brand400']))
        story.append(Spacer(1, 12))

        profile_rows = []
        fields = [
            ('Country',           assessment_data.get('country', '—')),
            ('Electricity',        f"{assessment_data.get('electricity_kwh', '—')} kWh/mo"),
            ('Vehicle Type',      assessment_data.get('vehicle_type', '—').title()),
            ('Vehicle Dist.',      f"{assessment_data.get('vehicle_km', '—')} km/mo"),
            ('Flight Freq.',      assessment_data.get('flight_type', '—').title()),
            ('Diet Type',         assessment_data.get('diet_type', '—').title()),
            ('Shopping',          assessment_data.get('shopping_freq', '—').title()),
            ('Recycling',         assessment_data.get('recycling', '—').title()),
        ]
        for i in range(0, len(fields), 2):
            row = []
            for j in [i, i+1]:
                if j < len(fields):
                    row.append(Paragraph(fields[j][0], _s(f'PK{j}', size=8, color=C['gray500'], bold=True)))
                    row.append(Paragraph(str(fields[j][1]), _s(f'PV{j}', size=10, color=C['gray900'], bold=True)))
                else:
                    row += [Paragraph('', sTD), Paragraph('', sTD)]
            profile_rows.append(row)

        profile_table = Table(profile_rows, colWidths=[W*0.20, W*0.30, W*0.20, W*0.30])
        profile_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), C['gray50']),
            ('ALIGN',      (0,0), (-1,-1), 'LEFT'),
            ('VALIGN',     (0,0), (-1,-1), 'MIDDLE'),
            ('TOPPADDING',    (0,0), (-1,-1), 12),
            ('BOTTOMPADDING', (0,0), (-1,-1), 12),
            ('LEFTPADDING',   (0,0), (-1,-1), 16),
            ('ROUNDEDCORNERS', [12, 12, 12, 12]),
        ]))
        story.append(profile_table)
        story.append(Spacer(1, 30))

        # ── EMISSIONS BREAKDOWN ───────────────────────────────────────────────
        story.append(Paragraph('Emissions Breakdown', sSec))
        story.append(GradientBar(W, 2, C['brand500'], C['brand400']))
        story.append(Spacer(1, 12))

        breakdown = assessment_data.get('breakdown', {})
        if breakdown:
            bk_data = [
                [Paragraph(h, _s('BTH', size=9, color=C['gray500'], align=TA_LEFT, bold=True)) for h in ['Category', 'kg CO₂e / Year', '% of Total']],
            ]
            total_calc = sum(breakdown.values()) or 1
            for name, val in breakdown.items():
                pct = val / total_calc * 100
                row = [
                    Paragraph(f'<b>{name.replace("_", " ").title()}</b>', sTD),
                    Paragraph(f'{int(val):,}', _s(f'BV{name}', size=10, color=C['brand700'], align=TA_LEFT, bold=True)),
                    Paragraph(f'{pct:.1f}%', _s(f'BP{name}', size=10, color=C['gray600'], align=TA_LEFT)),
                ]
                bk_data.append(row)

            bk_table = Table(bk_data, colWidths=[W*0.4, W*0.3, W*0.3])
            bk_table.setStyle(TableStyle([
                ('LINEBELOW', (0,0), (-1,-2), 1, C['gray200']),
                ('VALIGN',     (0,0), (-1,-1), 'MIDDLE'),
                ('TOPPADDING',    (0,0), (-1,-1), 12),
                ('BOTTOMPADDING', (0,0), (-1,-1), 12),
            ]))
            story.append(bk_table)
            story.append(Spacer(1, 30))

        # ── RECOMMENDATIONS ───────────────────────────────────────────────────
        story.append(Paragraph('Actionable Insights', sSec))
        story.append(GradientBar(W, 2, C['brand500'], C['brand400']))
        story.append(Spacer(1, 12))

        if recommendations:
            rec_data = []
            for i, rec in enumerate(recommendations[:8], 1):
                if isinstance(rec, dict):
                    text = rec.get('text', str(rec))
                else:
                    text = str(rec)
                rec_data.append([
                    Paragraph(f'<b>{i}.</b>', _s(f'RN{i}', size=11, color=C['brand600'], align=TA_LEFT, bold=True)),
                    Paragraph(text, sRec),
                ])
            rec_table = Table(rec_data, colWidths=[W*0.06, W*0.94])
            rec_table.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,-1), C['brand50']),
                ('VALIGN',     (0,0), (-1,-1), 'TOP'),
                ('TOPPADDING',    (0,0), (-1,-1), 12),
                ('BOTTOMPADDING', (0,0), (-1,-1), 12),
                ('ROUNDEDCORNERS', [12, 12, 12, 12]),
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
            'compliance documentation.'
        )
        story.append(Paragraph(disc, _s('Disc', size=8, color=C['gray500'], align=TA_JUSTIFY, leading=12)))

        doc.build(story, onFirstPage=_header_footer_carbon, onLaterPages=_header_footer_carbon)
        buffer.seek(0)
        return buffer

    # ── ESG Report ────────────────────────────────────────────────────────────

    def generate_enterprise_report(self, user_data: dict, assessment_data: dict, recommendations=None) -> str:
        """
        Generate a beautiful, professional ESG Readiness Report.
        """
        if recommendations is None:
            recommendations = assessment_data.get('recommendations', [])
        
        if not isinstance(recommendations, list):
            if isinstance(recommendations, dict):
                recommendations = list(recommendations.values())
            else:
                recommendations = []
            
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer, pagesize=A4,
            rightMargin=36, leftMargin=36,
            topMargin=60, bottomMargin=48,
            title='ESG Readiness Report',
            author='Carbon ESG Platform',
        )

        story = []
        W = A4[0] - 72

        sTitle = _s('ET', size=28, color=C['gray900'], align=TA_CENTER, bold=True, leading=34, after=4)
        sSub   = _s('ES', size=12, color=C['blue600'],  align=TA_CENTER, leading=16, after=24)
        sSec   = _s('ESecH', size=16, color=C['gray900'], bold=True, before=10, after=8)
        sBody  = _s('EBody', size=10, color=C['gray800'], leading=16, after=8)
        sTH    = _s('ETH', size=9, color=C['gray500'], align=TA_LEFT, bold=True)
        sTD    = _s('ETD', size=10, color=C['gray900'], align=TA_LEFT, leading=14)

        esg_score   = assessment_data.get('total_score', 0)
        esg_risk    = assessment_data.get('esg_risk', 'Medium')
        company     = assessment_data.get('company_name', user_data.get('username', 'Company'))
        industry    = assessment_data.get('industry', '—').title()
        env_score   = assessment_data.get('environmental_score', esg_score * 0.7)
        soc_score   = assessment_data.get('social_score', esg_score * 0.15)
        gov_score   = assessment_data.get('governance_score', esg_score * 0.15)

        risk_color = C['brand500'] if esg_risk == 'Low' else C['warning'] if esg_risk == 'Medium' else C['danger']

        # ── COVER ─────────────────────────────────────────────────────────────
        story.append(Spacer(1, 10))
        story.append(Paragraph('ESG Readiness Report', sTitle))
        story.append(Paragraph(f'Prepared for <b>{company}</b> · {industry}', sSub))

        # ESG Score hero (Rounded Card)
        hero_data = [
            [
                Paragraph(f'<b>{esg_score}</b><font size=14 color="{C["gray400"]}">/100</font>', _s('SV', size=36, color=C['blue900'], align=TA_CENTER, bold=True, leading=40)),
                Paragraph(f'<b>{esg_risk} Risk</b>', _s('RV', size=22, color=risk_color, align=TA_CENTER, bold=True, leading=26)),
            ],
            [
                Paragraph('Overall ESG Score', _s('SL', size=9, color=C['gray500'], align=TA_CENTER)),
                Paragraph('Risk Classification', _s('RL', size=9, color=C['gray500'], align=TA_CENTER)),
            ],
        ]
        hero_table = Table(hero_data, colWidths=[W/2]*2)
        hero_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), C['blue50']),
            ('LINEBETWEEN', (0,0), (-1,-1), 1, colors.HexColor('#dbeafe')),
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('TOPPADDING', (0,0), (-1,-1), 20),
            ('BOTTOMPADDING', (0,0), (-1,-1), 20),
            ('ROUNDEDCORNERS', [16, 16, 16, 16]),
        ]))
        story.append(hero_table)
        story.append(Spacer(1, 30))

        # ── ESG PILLAR SCORES ─────────────────────────────────────────────────
        story.append(Paragraph('Pillar Analysis', sSec))
        story.append(GradientBar(W, 2, C['blue600'], C['blue400']))
        story.append(Spacer(1, 12))

        pillars = [
            ('Environmental', env_score, 70, C['brand600']),
            ('Social', soc_score, 15, C['blue600']),
            ('Governance', gov_score, 15, colors.HexColor('#7c3aed')), # Violet-600
        ]

        pillar_data = []
        for name, score, weight, col in pillars:
            pillar_data.append([
                Paragraph(f'<b>{name}</b>', _s(f'PN{name}', size=11, color=C['gray900'], bold=True)),
                Paragraph(f'<b>{int(score)}</b>', _s(f'PS{name}', size=18, color=col, align=TA_RIGHT, bold=True)),
            ])
            pillar_data.append([
                Paragraph(f'Weight: {weight}%', _s(f'PW{name}', size=8, color=C['gray500'])),
                Paragraph('', _s(f'PE{name}', size=8)),
            ])

        pillar_table = Table(pillar_data, colWidths=[W*0.7, W*0.3])
        pillar_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), C['gray50']),
            ('LINEBELOW', (0,1), (-1,1), 1, C['white']),
            ('LINEBELOW', (0,3), (-1,3), 1, C['white']),
            ('VALIGN',     (0,0), (-1,-1), 'MIDDLE'),
            ('TOPPADDING',    (0,0), (-1,-1), 6),
            ('BOTTOMPADDING', (0,0), (-1,-1), 6),
            ('LEFTPADDING',   (0,0), (-1,-1), 16),
            ('RIGHTPADDING',  (0,0), (-1,-1), 16),
            ('ROUNDEDCORNERS', [12, 12, 12, 12]),
        ]))
        story.append(pillar_table)
        story.append(Spacer(1, 30))

        # ── KEY METRICS ────────────────────────────────────────────────────
        story.append(Paragraph('Key Performance Metrics', sSec))
        story.append(GradientBar(W, 2, C['blue600'], C['blue400']))
        story.append(Spacer(1, 12))

        metrics_data = [
            [Paragraph('Metric', sTH), Paragraph('Value', sTH)],
            [Paragraph('<b>Emissions per Employee</b>', sTD), Paragraph(f"{assessment_data.get('emissions_per_employee', 0)} tons CO₂e", sTD)],
            [Paragraph('<b>Energy Intensity</b>', sTD), Paragraph(f"{assessment_data.get('energy_intensity', 0)} kWh/emp", sTD)],
            [Paragraph('<b>Industry Benchmark</b>', sTD), Paragraph(f"{assessment_data.get('industry_benchmark', 0)} tons/emp", sTD)],
        ]
        metrics_table = Table(metrics_data, colWidths=[W*0.6, W*0.4])
        metrics_table.setStyle(TableStyle([
            ('LINEBELOW', (0,0), (-1,-2), 1, C['gray200']),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('TOPPADDING', (0,0), (-1,-1), 12),
            ('BOTTOMPADDING', (0,0), (-1,-1), 12),
        ]))
        story.append(metrics_table)
        story.append(Spacer(1, 30))

        # ── RECOMMENDATIONS ────────────────────────────────────────────────────
        if recommendations:
            story.append(Paragraph('Strategic Recommendations', sSec))
            story.append(GradientBar(W, 2, C['blue600'], C['blue400']))
            story.append(Spacer(1, 12))

            rec_data = []
            for i, rec in enumerate(recommendations[:6], 1):
                if isinstance(rec, dict):
                    txt = rec.get('text', str(rec))
                else:
                    txt = str(rec)
                rec_data.append([
                    Paragraph(f'<b>{i}.</b>', _s(f'RN{i}', size=11, color=C['blue600'], align=TA_LEFT, bold=True)),
                    Paragraph(txt, _s(f'RT{i}', size=10, color=C['gray800'], leading=15))
                ])

            rec_table = Table(rec_data, colWidths=[W*0.06, W*0.94])
            rec_table.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,-1), C['blue50']),
                ('VALIGN',     (0,0), (-1,-1), 'TOP'),
                ('TOPPADDING',    (0,0), (-1,-1), 12),
                ('BOTTOMPADDING', (0,0), (-1,-1), 12),
                ('ROUNDEDCORNERS', [12, 12, 12, 12]),
            ]))
            story.append(rec_table)
            story.append(Spacer(1, 24))

        # ── DISCLAIMER ────────────────────────────────────────────────────────
        story.append(SectionDivider(W))
        story.append(Spacer(1, 12))
        story.append(Paragraph(
            'This ESG readiness report is generated by the Carbon ESG Platform for educational and strategic awareness '
            'purposes only. It does not constitute formal ESG certification, audit, or regulatory compliance documentation.',
            _s('EDisc', size=8, color=C['gray500'], align=TA_JUSTIFY, leading=12)
        ))

        doc.build(story, onFirstPage=_header_footer_esg, onLaterPages=_header_footer_esg)
        buffer.seek(0)
        return buffer

    # ── Certificate ───────────────────────────────────────────────────────────
# ── Certificate ───────────────────────────────────────────────────────────

    def generate_certificate(self, user_data: dict, assessment_type: str, score) -> str:
        """
        Generate a highly creative, single-page, premium certificate using absolute Canvas drawing.
        Incorporates organic fluid shapes and a Royal Gold/Emerald aesthetic.
        """
        from reportlab.pdfgen import canvas
        
        page_w, page_h = landscape(A4)
        buffer = io.BytesIO()
        
        # Using Canvas directly guarantees a strict single-page layout
        c = canvas.Canvas(buffer, pagesize=(page_w, page_h))

        # Premium Color Palette
        royal_emerald = colors.HexColor('#064e3b') # Deep rich background
        deep_accent   = colors.HexColor('#022c22') # Shadow/depth layer
        gold          = colors.HexColor('#fbbf24') # Royal Gold
        gold_light    = colors.HexColor('#fef08a') # Highlight Gold
        gold_dark     = colors.HexColor('#b45309') # Ribbon shadow
        white         = colors.white
        
        # 1. Base Background
        c.setFillColor(royal_emerald)
        c.rect(0, 0, page_w, page_h, stroke=0, fill=1)

        # 2. Fluid / Organic Background Shapes (Fluid Intelligence design)
        # Top-right organic wave
        c.setFillColor(deep_accent)
        p = c.beginPath()
        p.moveTo(page_w, page_h)
        p.lineTo(page_w / 2, page_h)
        p.curveTo(page_w * 0.7, page_h * 0.8, page_w * 0.8, page_h * 0.4, page_w, page_h * 0.3)
        p.close()
        c.drawPath(p, stroke=0, fill=1)

        # Bottom-left organic wave
        p = c.beginPath()
        p.moveTo(0, 0)
        p.lineTo(page_w * 0.4, 0)
        p.curveTo(page_w * 0.3, page_h * 0.2, page_w * 0.1, page_h * 0.4, 0, page_h * 0.6)
        p.close()
        c.drawPath(p, stroke=0, fill=1)

        # 3. Outer Premium Gold Borders
        c.setStrokeColor(gold)
        c.setLineWidth(2.5)
        c.roundRect(30, 30, page_w - 60, page_h - 60, 15, stroke=1, fill=0)
        
        c.setStrokeColor(gold_light)
        c.setLineWidth(0.8)
        c.roundRect(38, 38, page_w - 76, page_h - 76, 10, stroke=1, fill=0)

        # 4. Sharp Corner Accents
        for x, y, ang in [
            (30, page_h - 30, 0),
            (page_w - 30, page_h - 30, 90),
            (page_w - 30, 30, 180),
            (30, 30, 270),
        ]:
            c.saveState()
            c.translate(x, y)
            c.rotate(ang)
            c.setFillColor(gold)
            p = c.beginPath()
            p.moveTo(0, 0)
            p.lineTo(35, 0)
            p.lineTo(0, -35)
            p.close()
            c.drawPath(p, stroke=0, fill=1)
            c.restoreState()

        # 5. Typography & Content Alignment
        c.setFillColor(gold_light)
        c.setFont(FONT_BOLD, 14)
        c.drawCentredString(page_w / 2, page_h - 90, "C A R B O N . E S G   P L A T F O R M")

        c.setFillColor(white)
        c.setFont(FONT_BOLD, 46)
        c.drawCentredString(page_w / 2, page_h - 165, "CERTIFICATE OF EXCELLENCE")

        c.setFillColor(gold_light)
        c.setFont(FONT_LIGHT, 16)
        c.drawCentredString(page_w / 2, page_h - 220, "This is proudly presented to")

        username = user_data.get('username', 'Participant')
        c.setFillColor(gold)
        c.setFont(FONT_BOLD, 54)
        c.drawCentredString(page_w / 2, page_h - 290, username.upper())

        c.setFillColor(white)
        c.setFont(FONT_LIGHT, 15)
        c.drawCentredString(page_w / 2, page_h - 340, "for outstanding performance and successful completion of the")

        c.setFillColor(gold_light)
        c.setFont(FONT_BOLD, 22)
        c.drawCentredString(page_w / 2, page_h - 380, assessment_type.upper())

        # 6. Bottom Metadata (Signatures & Date)
        # Left Side: Date
        c.setFillColor(white)
        c.setFont(FONT_BOLD, 14)
        c.drawString(100, 120, datetime.now().strftime("%d %B %Y"))
        
        c.setStrokeColor(gold)
        c.setLineWidth(1)
        c.line(100, 110, 280, 110)
        
        c.setFillColor(gold_light)
        c.setFont(FONT_LIGHT, 10)
        c.drawString(100, 95, "DATE OF ISSUE")

        # Right Side: Score
        c.setFillColor(white)
        c.setFont(FONT_BOLD, 14)
        c.drawRightString(page_w - 100, 120, f"Score: {score} / 100")
        
        c.line(page_w - 280, 110, page_w - 100, 110)
        
        c.setFillColor(gold_light)
        c.setFont(FONT_LIGHT, 10)
        c.drawRightString(page_w - 100, 95, "AUTHORISED SIGNATURE")

        # 7. Center Gold Seal with Ribbon
        cx, cy = page_w / 2, 115
        r_outer = 45
        r_inner = 35

        # Ribbon Tails
        c.setFillColor(gold_dark)

        p1 = c.beginPath()
        p1.moveTo(cx - 20, cy - 30)
        p1.lineTo(cx - 45, cy - 90)
        p1.lineTo(cx - 10, cy - 75)
        p1.close()
        c.drawPath(p1, stroke=0, fill=1)

        p2 = c.beginPath()
        p2.moveTo(cx + 20, cy - 30)
        p2.lineTo(cx + 45, cy - 90)
        p2.lineTo(cx + 10, cy - 75)
        p2.close()
        c.drawPath(p2, stroke=0, fill=1)

        # Multi-layer Seal
        c.setFillColor(gold)
        c.circle(cx, cy, r_outer, stroke=0, fill=1)
        
        c.setFillColor(royal_emerald)
        c.circle(cx, cy, r_inner, stroke=0, fill=1)
        
        c.setStrokeColor(gold_light)
        c.setLineWidth(1)
        c.circle(cx, cy, r_inner - 4, stroke=1, fill=0)

        # Star / Center Icon
        c.setFillColor(gold)
        c.setFont(FONT_BOLD, 26)
        c.drawCentredString(cx, cy - 9, "★")

        # Compile and save the single-page PDF
        c.showPage()
        c.save()
        buffer.seek(0)

        return buffer