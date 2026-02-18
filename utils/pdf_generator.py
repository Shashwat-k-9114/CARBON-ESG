from reportlab.lib.pagesizes import letter, A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, cm, mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, Flowable
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.graphics.shapes import Drawing, Line, Rect, String
from reportlab.graphics.charts.barcharts import VerticalBarChart
from reportlab.graphics.charts.piecharts import Pie
from reportlab.graphics.widgets.signsandsymbols import SmileyFace
from datetime import datetime
import os
import math

# Try to register custom fonts - if not available, Helvetica will be used
try:
    pdfmetrics.registerFont(TTFont('Roboto-Light', 'Roboto-Light.ttf'))
    pdfmetrics.registerFont(TTFont('Roboto-Regular', 'Roboto-Regular.ttf'))
    pdfmetrics.registerFont(TTFont('Roboto-Medium', 'Roboto-Medium.ttf'))
    pdfmetrics.registerFont(TTFont('Roboto-Bold', 'Roboto-Bold.ttf'))
    FONT_REGULAR = 'Roboto-Regular'
    FONT_BOLD = 'Roboto-Bold'
    FONT_LIGHT = 'Roboto-Light'
    FONT_MEDIUM = 'Roboto-Medium'
except:
    FONT_REGULAR = 'Helvetica'
    FONT_BOLD = 'Helvetica-Bold'
    FONT_LIGHT = 'Helvetica'
    FONT_MEDIUM = 'Helvetica-Bold'

class HorizontalLine(Flowable):
    """Custom horizontal line with gradient effect"""
    def __init__(self, width, color=colors.HexColor('#2E7D32'), thickness=1):
        Flowable.__init__(self)
        self.width = width
        self.color = color
        self.thickness = thickness

    def draw(self):
        self.canv.setStrokeColor(self.color)
        self.canv.setLineWidth(self.thickness)
        self.canv.line(0, 0, self.width, 0)

class GradientBackground(Flowable):
    """Modern gradient background for sections"""
    def __init__(self, width, height, start_color, end_color):
        Flowable.__init__(self)
        self.width = width
        self.height = height
        self.start_color = start_color
        self.end_color = end_color

    def draw(self):
        # Create a simple gradient effect with overlapping rectangles
        steps = 20
        for i in range(steps):
            x = (i / steps) * self.width
            w = self.width / steps
            ratio = i / steps
            # Interpolate between colors
            r = self.start_color.red + (self.end_color.red - self.start_color.red) * ratio
            g = self.start_color.green + (self.end_color.green - self.start_color.green) * ratio
            b = self.start_color.blue + (self.end_color.blue - self.start_color.blue) * ratio
            color = colors.Color(r, g, b)
            self.canv.setFillColor(color)
            self.canv.rect(x, 0, w, self.height, stroke=0, fill=1)

class PDFGenerator:
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self.setup_styles()
        self.colors = {
            'primary': colors.HexColor('#2E7D32'),
            'secondary': colors.HexColor('#4CAF50'),
            'accent': colors.HexColor('#8BC34A'),
            'dark': colors.HexColor('#1B5E20'),
            'light': colors.HexColor('#E8F5E9'),
            'warning': colors.HexColor('#FF9800'),
            'danger': colors.HexColor('#F44336'),
            'info': colors.HexColor('#2196F3'),
            'gray1': colors.HexColor('#F5F5F5'),
            'gray2': colors.HexColor('#EEEEEE'),
            'gray3': colors.HexColor('#E0E0E0'),
            'text': colors.HexColor('#333333'),
            'text_light': colors.HexColor('#757575'),
        }
        
    def setup_styles(self):
        """Setup custom styles for the PDF"""
        
        # Title style - large and bold
        self.styles.add(ParagraphStyle(
            name='ModernTitle',
            parent=self.styles['Heading1'],
            fontName=FONT_BOLD,
            fontSize=28,
            textColor=colors.HexColor('#2E7D32'),
            alignment=TA_CENTER,
            spaceAfter=10,
            leading=34
        ))
        
        # Subtitle style
        self.styles.add(ParagraphStyle(
            name='ModernSubtitle',
            parent=self.styles['Heading2'],
            fontName=FONT_MEDIUM,
            fontSize=16,
            textColor=colors.HexColor('#388E3C'),
            alignment=TA_CENTER,
            spaceAfter=20,
            leading=22
        ))
        
        # Section header style
        self.styles.add(ParagraphStyle(
            name='SectionHeader',
            parent=self.styles['Heading3'],
            fontName=FONT_BOLD,
            fontSize=14,
            textColor=colors.HexColor('#2E7D32'),
            alignment=TA_LEFT,
            spaceAfter=12,
            spaceBefore=15,
            leading=18
        ))
        
        # Normal text with better spacing
        self.styles.add(ParagraphStyle(
            name='ModernNormal',
            parent=self.styles['Normal'],
            fontName=FONT_REGULAR,
            fontSize=10,
            leading=14,
            textColor=colors.HexColor('#333333'),
            spaceAfter=10,
            alignment=TA_LEFT
        ))
        
        # Small print / disclaimer
        self.styles.add(ParagraphStyle(
            name='ModernSmall',
            parent=self.styles['Normal'],
            fontName=FONT_LIGHT,
            fontSize=8,
            leading=11,
            textColor=colors.HexColor('#757575'),
            alignment=TA_CENTER
        ))
        
        # Header for tables
        self.styles.add(ParagraphStyle(
            name='TableHeader',
            parent=self.styles['Normal'],
            fontName=FONT_BOLD,
            fontSize=10,
            textColor=colors.white,
            alignment=TA_CENTER,
            leading=14
        ))
        
        # Table cell text
        self.styles.add(ParagraphStyle(
            name='TableCell',
            parent=self.styles['Normal'],
            fontName=FONT_REGULAR,
            fontSize=9,
            textColor=colors.HexColor('#333333'),
            alignment=TA_CENTER,
            leading=12
        ))
        
        # Score display style
        self.styles.add(ParagraphStyle(
            name='ScoreStyle',
            parent=self.styles['Normal'],
            fontName=FONT_BOLD,
            fontSize=36,
            textColor=colors.HexColor('#2E7D32'),
            alignment=TA_CENTER,
            leading=42
        ))
        
        # Certificate title style
        self.styles.add(ParagraphStyle(
            name='CertificateTitle',
            parent=self.styles['Heading1'],
            fontName=FONT_BOLD,
            fontSize=42,
            textColor=colors.HexColor('#2E7D32'),
            alignment=TA_CENTER,
            spaceAfter=30,
            leading=48
        ))
        
        # Footer style
        self.styles.add(ParagraphStyle(
            name='ModernFooter',
            parent=self.styles['Normal'],
            fontName=FONT_LIGHT,
            fontSize=7,
            textColor=colors.HexColor('#9E9E9E'),
            alignment=TA_CENTER,
            leading=10
        ))
        
    def create_header(self, story, title, subtitle=None):
        """Create a modern header with gradient line"""
        story.append(Paragraph(title, self.styles['ModernTitle']))
        if subtitle:
            story.append(Paragraph(subtitle, self.styles['ModernSubtitle']))
        story.append(Spacer(1, 5))
        story.append(HorizontalLine(500, colors.HexColor('#2E7D32'), 2))
        story.append(Spacer(1, 20))
    
    def create_info_box(self, story, label, value, icon="•", color=None):
        """Create a styled info box"""
        if color is None:
            color = self.colors['primary']
        
        data = [[
            Paragraph(f"<font color='{color}'>{icon}</font>", self.styles['ModernNormal']),
            Paragraph(f"<b>{label}:</b> {value}", self.styles['ModernNormal'])
        ]]
        table = Table(data, colWidths=[20, 450])
        table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('LEFTPADDING', (0, 0), (0, 0), 0),
            ('RIGHTPADDING', (1, 0), (1, 0), 0),
        ]))
        story.append(table)
        story.append(Spacer(1, 5))
    
    def create_score_card(self, story, score, label, color=None):
        """Create a modern score card"""
        if color is None:
            color = self.colors['primary']
        
        # Background rectangle
        data = [[
            Paragraph(f"<para alignment='center'><font size=36 color='{color}'><b>{score}</b></font><br/><font size=11>{label}</font></para>", 
                    self.styles['ModernNormal'])
        ]]
        table = Table(data, colWidths=[200])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), self.colors['gray1']),
            ('BOX', (0, 0), (-1, -1), 1, self.colors['gray3']),
            ('ROUNDEDCORNERS', [10, 10, 10, 10]),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 20),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 20),
        ]))
        story.append(table)
        story.append(Spacer(1, 15))
    
    def create_progress_bar(self, story, label, value, max_value, color=None):
        """Create a modern progress bar"""
        if color is None:
            color = self.colors['primary']
        
        percentage = (value / max_value) * 100 if max_value else 0
        bar_width = 300
        filled_width = bar_width * (percentage / 100)
        
        # Create a table for the bar
        data = [
            [Paragraph(f"<b>{label}</b>", self.styles['ModernNormal']), 
             Paragraph(f"{value:.1f}", self.styles['ModernNormal'])],
            ['', '']
        ]
        table = Table(data, colWidths=[400, 100])
        table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('LINEABOVE', (0, 1), (-1, -1), 1, self.colors['gray3']),
            ('BACKGROUND', (0, 1), (0, 1), self.colors['gray2']),
        ]))
        
        # Draw the bar (simplified - in real implementation, you'd use a custom flowable)
        story.append(table)
        story.append(Spacer(1, 5))
    
    def generate_individual_report(self, user_data, calculation_result):
        """
        Generate a beautiful individual carbon footprint report
        """
        filename = f"carbon_report_{user_data['username']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        filepath = os.path.join('static', 'reports', filename)
        
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        doc = SimpleDocTemplate(
            filepath,
            pagesize=A4,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=72
        )
        
        story = []
        
        # ===== MODERN HEADER =====
        story.append(Spacer(1, 20))
        story.append(Paragraph("🌱 CARBON FOOTPRINT REPORT", self.styles['ModernTitle']))
        story.append(Paragraph("AI-Powered Sustainability Analysis", self.styles['ModernSubtitle']))
        story.append(Spacer(1, 5))
        story.append(HorizontalLine(500, colors.HexColor('#2E7D32'), 3))
        story.append(Spacer(1, 20))
        
        # ===== USER INFO WITH ICONS =====
        self.create_info_box(story, "Report For", user_data['username'], "👤")
        self.create_info_box(story, "Date", datetime.now().strftime('%B %d, %Y'), "📅")
        self.create_info_box(story, "Report ID", f"CF-{datetime.now().strftime('%Y%m%d%H%M%S')}", "🔖")
        story.append(Spacer(1, 20))
        
        # ===== SCORE CARD =====
        footprint = calculation_result['total_footprint']
        level = calculation_result['carbon_level']
        
        # Color based on level
        if 'Low' in level:
            color = colors.HexColor('#4CAF50')
        elif 'Medium' in level:
            color = colors.HexColor('#FF9800')
        else:
            color = colors.HexColor('#F44336')
        
        # Create a nice score display
        score_data = [[
            Paragraph(f"<para alignment='center'><font size={48} color='{color}'><b>{footprint:,.0f}</b></font><br/><font size=12>kg CO₂e</font><br/><font size=14 color='{color}'><b>{level}</b></font><br/><font size=9 color='#757575'>Annual Carbon Footprint</font></para>",
                     self.styles['ModernNormal'])
        ]]
        score_table = Table(score_data, colWidths=[450])
        score_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#F8F9FA')),
            ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#E0E0E0')),
            ('ROUNDEDCORNERS', [15, 15, 15, 15]),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 30),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 30),
        ]))
        story.append(score_table)
        story.append(Spacer(1, 25))
        
        # ===== EMISSIONS BREAKDOWN TABLE =====
        story.append(Paragraph("📊 Emissions Breakdown", self.styles['SectionHeader']))
        story.append(Spacer(1, 5))
        
        breakdown = calculation_result['breakdown']
        
        # Prepare data for table
        table_data = [
            ['Category', 'Annual Emissions', 'Percentage', 'Impact'],
        ]
        
        categories = [
            ('Electricity', breakdown['electricity'], '⚡'),
            ('Transport', breakdown['transport'], '🚗'),
            ('Diet', breakdown['diet'], '🍽️'),
            ('Shopping', breakdown['shopping'], '🛍️'),
            ('Recycling Credit', breakdown['recycling_credit'], '♻️'),
        ]
        
        for cat_name, cat_value, icon in categories:
            percentage = (cat_value / footprint * 100) if footprint else 0
            if cat_value < 0:
                impact = "🌱 Credit"
                row_color = colors.HexColor('#E8F5E9')
            elif percentage < 15:
                impact = "✅ Low"
                row_color = colors.HexColor('#F1F8E9')
            elif percentage < 30:
                impact = "⚠️ Medium"
                row_color = colors.HexColor('#FFF3E0')
            else:
                impact = "🔴 High"
                row_color = colors.HexColor('#FFEBEE')
            
            table_data.append([
                f"{icon} {cat_name}",
                f"{cat_value:,.0f} kg",
                f"{percentage:.1f}%",
                impact
            ])
        
        # Add total row
        table_data.append([
            '<b>TOTAL</b>',
            f'<b>{footprint:,.0f} kg</b>',
            '<b>100%</b>',
            ''
        ])
        
        # Create the table
        col_widths = [180, 100, 80, 100]
        table = Table(table_data, colWidths=col_widths, repeatRows=1)
        
        # Style the table
        table_style = [
            # Header
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2E7D32')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), FONT_BOLD),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('TOPPADDING', (0, 0), (-1, 0), 12),
            
            # Body
            ('FONTNAME', (0, 1), (-1, -2), FONT_REGULAR),
            ('FONTSIZE', (0, 1), (-1, -2), 9),
            ('ALIGN', (1, 1), (-1, -2), 'CENTER'),
            ('ALIGN', (0, 1), (0, -2), 'LEFT'),
            
            # Grid
            ('GRID', (0, 0), (-1, -2), 1, colors.HexColor('#E0E0E0')),
            ('LINEBELOW', (0, -1), (-1, -1), 2, colors.HexColor('#2E7D32')),
            ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#F5F5F5')),
            ('FONTNAME', (0, -1), (-1, -1), FONT_BOLD),
        ]
        
        # Add alternating row colors
        for i in range(1, len(table_data)-1):
            if i % 2 == 0:
                table_style.append(('BACKGROUND', (0, i), (-1, i), colors.HexColor('#F9F9F9')))
        
        table.setStyle(TableStyle(table_style))
        story.append(table)
        story.append(Spacer(1, 25))
        
        # ===== METHODOLOGY CARD =====
        story.append(Paragraph("🔬 Calculation Methodology", self.styles['SectionHeader']))
        story.append(Spacer(1, 5))
        
        ml_pred = calculation_result.get('ml_prediction', 0)
        rule_pred = calculation_result.get('rule_based', 0)
        
        method_data = [
            ['Method', 'Value', 'Weight'],
            ['🤖 Machine Learning', f"{ml_pred:,.0f} kg CO₂e", '70%'],
            ['📐 Rule-Based (DEFRA)', f"{rule_pred:,.0f} kg CO₂e", '30%'],
        ]
        
        method_table = Table(method_data, colWidths=[200, 150, 100])
        method_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4CAF50')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), FONT_BOLD),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#E0E0E0')),
            ('BACKGROUND', (0, 1), (-1, 1), colors.HexColor('#F1F8E9')),
            ('BACKGROUND', (0, 2), (-1, 2), colors.HexColor('#F9F9F9')),
            ('ROUNDEDCORNERS', [5, 5, 5, 5]),
        ]))
        story.append(method_table)
        story.append(Spacer(1, 5))
        story.append(Paragraph("<i>Final result uses weighted average for optimal accuracy</i>", 
                               self.styles['ModernSmall']))
        story.append(Spacer(1, 20))
        
        # ===== RECOMMENDATIONS =====
        story.append(Paragraph("💡 Personalized Recommendations", self.styles['SectionHeader']))
        story.append(Spacer(1, 5))
        
        for i, suggestion in enumerate(calculation_result['suggestions'][:5], 1):
            # Create a nice bullet point
            bullet_data = [[
                Paragraph(f"<font color='#2E7D32'>●</font>", self.styles['ModernNormal']),
                Paragraph(f"<b>{i}.</b> {suggestion}", self.styles['ModernNormal'])
            ]]
            bullet_table = Table(bullet_data, colWidths=[20, 480])
            bullet_table.setStyle(TableStyle([
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('LEFTPADDING', (0, 0), (0, 0), 0),
            ]))
            story.append(bullet_table)
            story.append(Spacer(1, 5))
        
        story.append(Spacer(1, 20))
        
        # ===== INPUT SUMMARY =====
        story.append(Paragraph("📝 Your Input Summary", self.styles['SectionHeader']))
        story.append(Spacer(1, 5))
        
        inputs = calculation_result.get('inputs', {})
        input_data = [
            ['Category', 'Value'],
            ['Country', inputs.get('country', 'N/A')],
            ['Electricity', f"{inputs.get('electricity_kwh', 0)} kWh/month"],
            ['Vehicle', inputs.get('vehicle_type', 'none').title()],
            ['Distance', f"{inputs.get('vehicle_km', 0)} km/month"],
            ['Flights', inputs.get('flight_type', 'none').title()],
            ['Diet', inputs.get('diet_type', 'mixed').title()],
            ['Shopping', inputs.get('shopping_freq', 'medium').title()],
            ['Recycling', inputs.get('recycling', 'no').title()],
        ]
        
        input_table = Table(input_data, colWidths=[150, 350])
        input_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#8BC34A')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), FONT_BOLD),
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#E0E0E0')),
            ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#F9F9F9')),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('ROUNDEDCORNERS', [5, 5, 5, 5]),
        ]))
        
        # Add alternating colors
        for i in range(1, len(input_data)):
            if i % 2 == 1:
                input_table.setStyle(TableStyle([('BACKGROUND', (0, i), (-1, i), colors.HexColor('#F5F5F5'))]))
        
        story.append(input_table)
        story.append(Spacer(1, 30))
        
        # ===== DISCLAIMER =====
        story.append(HorizontalLine(500, colors.HexColor('#E0E0E0'), 1))
        story.append(Spacer(1, 10))
        disclaimer_text = """
        <para alignment='center'>
        <font color='#757575' size='8'>
        This report is generated by an AI-based estimation platform for educational purposes only. 
        The results are approximations and should not be used for formal carbon accounting or 
        regulatory compliance. Always consult certified sustainability professionals for accurate assessments.
        </font>
        </para>
        """
        story.append(Paragraph(disclaimer_text, self.styles['ModernSmall']))
        story.append(Spacer(1, 10))
        
        # ===== FOOTER =====
        footer_text = f"""
        Generated by Carbon ESG Platform • {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} • Page 1 of 1
        """
        story.append(Paragraph(footer_text, self.styles['ModernFooter']))
        
        # Build PDF
        doc.build(story)
        return filename
    
    def generate_enterprise_report(self, user_data, calculation_result, inputs):
        """
        Generate a beautiful enterprise ESG assessment report
        """
        filename = f"esg_report_{user_data['username']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        filepath = os.path.join('static', 'reports', filename)
        
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        doc = SimpleDocTemplate(
            filepath,
            pagesize=A4,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=72
        )
        
        story = []
        
        # ===== MODERN HEADER =====
        story.append(Spacer(1, 20))
        story.append(Paragraph("🏢 ESG READINESS ASSESSMENT", self.styles['ModernTitle']))
        story.append(Paragraph("Corporate Sustainability Report", self.styles['ModernSubtitle']))
        story.append(Spacer(1, 5))
        story.append(HorizontalLine(500, colors.HexColor('#2E7D32'), 3))
        story.append(Spacer(1, 20))
        
        # ===== COMPANY INFO =====
        self.create_info_box(story, "Company", inputs.get('company_name', 'N/A'), "🏛️")
        self.create_info_box(story, "Industry", inputs.get('industry', 'N/A'), "🏭")
        self.create_info_box(story, "Employees", f"{inputs.get('employees', 0):,}", "👥")
        self.create_info_box(story, "Assessment Date", datetime.now().strftime('%B %d, %Y'), "📅")
        self.create_info_box(story, "Report ID", f"ESG-{datetime.now().strftime('%Y%m%d%H%M%S')}", "🔖")
        story.append(Spacer(1, 20))
        
        # ===== ESG SCORE CARD =====
        total_score = calculation_result['total_score']
        risk_level = calculation_result['esg_risk']
        
        # Color based on score
        if total_score >= 70:
            score_color = colors.HexColor('#4CAF50')
            risk_color = colors.HexColor('#4CAF50')
        elif total_score >= 50:
            score_color = colors.HexColor('#FF9800')
            risk_color = colors.HexColor('#FF9800')
        else:
            score_color = colors.HexColor('#F44336')
            risk_color = colors.HexColor('#F44336')
        
        # Create a nice score display
        score_data = [[
            Paragraph(f"<para alignment='center'><font size={48} color='{score_color}'><b>{total_score}</b></font><br/><font size=12>/100</font><br/><font size=14 color='{score_color}'><b>ESG Score</b></font></para>",
                     self.styles['ModernNormal']),
            Paragraph(f"<para alignment='center'><font size={48} color='{risk_color}'><b>●</b></font><br/><font size=12>Risk Level</font><br/><font size=14 color='{risk_color}'><b>{risk_level}</b></font></para>",
                     self.styles['ModernNormal'])
        ]]
        score_table = Table(score_data, colWidths=[225, 225])
        score_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#F8F9FA')),
            ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#E0E0E0')),
            ('ROUNDEDCORNERS', [15, 15, 15, 15]),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 30),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 30),
        ]))
        story.append(score_table)
        story.append(Spacer(1, 25))
        
        # ===== COMPONENT SCORES =====
        story.append(Paragraph("📊 ESG Component Analysis", self.styles['SectionHeader']))
        story.append(Spacer(1, 5))
        
        component_data = [
            ['Component', 'Score', 'Weight', 'Contribution'],
            ['🌿 Environmental', 
             f"{calculation_result['environmental_score']:.1f}", 
             '70%',
             f"{calculation_result['environmental_score']:.1f}"],
            ['👥 Social', 
             f"{calculation_result['social_score']:.1f}", 
             '15%',
             f"{calculation_result['social_score']:.1f}"],
            ['⚖️ Governance', 
             f"{calculation_result['governance_score']:.1f}", 
             '15%',
             f"{calculation_result['governance_score']:.1f}"],
        ]
        
        component_table = Table(component_data, colWidths=[150, 100, 100, 100])
        component_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2E7D32')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), FONT_BOLD),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#E0E0E0')),
            ('BACKGROUND', (0, 1), (-1, 1), colors.HexColor('#E8F5E9')),
            ('BACKGROUND', (0, 2), (-1, 2), colors.HexColor('#F1F8E9')),
            ('BACKGROUND', (0, 3), (-1, 3), colors.HexColor('#F9F9F9')),
            ('ROUNDEDCORNERS', [5, 5, 5, 5]),
        ]))
        story.append(component_table)
        story.append(Spacer(1, 25))
        
        # ===== KEY METRICS =====
        story.append(Paragraph("📈 Key Performance Metrics", self.styles['SectionHeader']))
        story.append(Spacer(1, 5))
        
        metrics_data = [
            ['Metric', 'Value', 'Benchmark', 'Status'],
            ['Emissions per Employee', 
             f"{calculation_result['emissions_per_employee']:.1f} tons CO₂e", 
             '2.5 tons',
             '✅' if calculation_result['emissions_per_employee'] < 2.5 else '⚠️'],
            ['Energy Intensity', 
             f"{calculation_result['energy_intensity']:.1f} kWh/employee", 
             '< 800 kWh',
             '✅' if calculation_result['energy_intensity'] < 800 else '⚠️'],
            ['Cloud Usage', 
             'Yes' if inputs.get('cloud_usage') == 'yes' else 'No', 
             'Recommended: Yes',
             '✅' if inputs.get('cloud_usage') == 'yes' else '⚠️'],
            ['Waste Management', 
             f"Level {inputs.get('waste_management', 0)}/5", 
             'Target: 4+',
             '✅' if inputs.get('waste_management', 0) >= 4 else '⚠️'],
        ]
        
        metrics_table = Table(metrics_data, colWidths=[180, 100, 100, 70])
        metrics_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4CAF50')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), FONT_BOLD),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#E0E0E0')),
            ('ROUNDEDCORNERS', [5, 5, 5, 5]),
        ]))
        
        # Add alternating colors
        for i in range(1, len(metrics_data)):
            if i % 2 == 0:
                metrics_table.setStyle(TableStyle([('BACKGROUND', (0, i), (-1, i), colors.HexColor('#F9F9F9'))]))
        
        story.append(metrics_table)
        story.append(Spacer(1, 25))
        
        # ===== STRATEGIC RECOMMENDATIONS =====
        story.append(Paragraph("💡 Strategic Recommendations", self.styles['SectionHeader']))
        story.append(Spacer(1, 5))
        
        for i, recommendation in enumerate(calculation_result['recommendations'][:6], 1):
            # Determine icon based on content
            if 'carbon' in recommendation.lower() or 'emission' in recommendation.lower():
                icon = '🌿'
            elif 'social' in recommendation.lower() or 'employee' in recommendation.lower():
                icon = '👥'
            elif 'governance' in recommendation.lower() or 'board' in recommendation.lower():
                icon = '⚖️'
            elif 'risk' in recommendation.lower():
                icon = '⚠️'
            elif 'audit' in recommendation.lower():
                icon = '🔍'
            elif 'cloud' in recommendation.lower():
                icon = '☁️'
            else:
                icon = '📋'
            
            bullet_data = [[
                Paragraph(f"<font color='#2E7D32'>{icon}</font>", self.styles['ModernNormal']),
                Paragraph(f"<b>{i}.</b> {recommendation}", self.styles['ModernNormal'])
            ]]
            bullet_table = Table(bullet_data, colWidths=[20, 480])
            bullet_table.setStyle(TableStyle([
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('LEFTPADDING', (0, 0), (0, 0), 0),
            ]))
            story.append(bullet_table)
            story.append(Spacer(1, 5))
        
        story.append(Spacer(1, 20))
        
        # ===== 90-DAY ACTION PLAN =====
        story.append(Paragraph("📅 90-Day Action Plan", self.styles['SectionHeader']))
        story.append(Spacer(1, 5))
        
        action_data = [
            ['Phase', 'Timeline', 'Actions'],
            ['🟢 Awareness', 'Month 1', '• Conduct ESG baseline\n• Form ESG committee\n• Set initial KPIs'],
            ['🟡 Implementation', 'Month 2', '• Employee awareness program\n• Track energy metrics\n• Review supply chain'],
            ['🔵 Review', 'Month 3', '• Analyze Q1 data\n• Prepare internal report\n• Plan next phase'],
        ]
        
        action_table = Table(action_data, colWidths=[100, 100, 300])
        action_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2E7D32')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), FONT_BOLD),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#E0E0E0')),
            ('BACKGROUND', (0, 1), (-1, 1), colors.HexColor('#E8F5E9')),
            ('BACKGROUND', (0, 2), (-1, 2), colors.HexColor('#F1F8E9')),
            ('BACKGROUND', (0, 3), (-1, 3), colors.HexColor('#F9F9F9')),
            ('ROUNDEDCORNERS', [5, 5, 5, 5]),
        ]))
        story.append(action_table)
        story.append(Spacer(1, 30))
        
        # ===== METHODOLOGY =====
        story.append(Paragraph("🔬 Assessment Methodology", self.styles['SectionHeader']))
        story.append(Spacer(1, 5))
        
        methodology_text = """
        <para>
        This ESG assessment uses a <b>Decision Tree Classifier</b> trained on industry benchmarks 
        and incorporates your company's operational data across three pillars:
        </para>
        """
        story.append(Paragraph(methodology_text, self.styles['ModernNormal']))
        story.append(Spacer(1, 5))
        
        pillars_data = [
            ['🌿 Environmental (70%)', 'Climate impact, resource efficiency, waste management'],
            ['👥 Social (15%)', 'Employee welfare, community engagement, diversity'],
            ['⚖️ Governance (15%)', 'Leadership accountability, transparency, ethics'],
        ]
        
        pillars_table = Table(pillars_data, colWidths=[150, 350])
        pillars_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), FONT_REGULAR),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ]))
        story.append(pillars_table)
        story.append(Spacer(1, 20))
        
        # ===== DISCLAIMER =====
        story.append(HorizontalLine(500, colors.HexColor('#E0E0E0'), 1))
        story.append(Spacer(1, 10))
        disclaimer_text = """
        <para alignment='center'>
        <font color='#757575' size='8'>
        This ESG readiness assessment is an AI-powered educational tool. It does not constitute formal 
        ESG certification, audit, or investment advice. For formal ESG reporting, engage qualified 
        sustainability consultants and follow established frameworks (GRI, SASB, TCFD).
        </font>
        </para>
        """
        story.append(Paragraph(disclaimer_text, self.styles['ModernSmall']))
        story.append(Spacer(1, 10))
        
        # ===== FOOTER =====
        footer_text = f"""
        Generated by Carbon ESG Platform • {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} • Page 1 of 1
        """
        story.append(Paragraph(footer_text, self.styles['ModernFooter']))
        
        # Build PDF
        doc.build(story)
        return filename
    
    def generate_certificate(self, user_data, assessment_type, score):
        """
        Generate a beautiful participation certificate
        """
        filename = f"certificate_{user_data['username']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        filepath = os.path.join('static', 'reports', filename)
        
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        doc = SimpleDocTemplate(
            filepath,
            pagesize=letter,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=72
        )
        
        story = []
        
        # ===== DECORATIVE BORDER =====
        # This would be a complex border - simplified version
        story.append(Spacer(1, 30))
        
        # ===== GOLD SEAL EFFECT =====
        seal_color = colors.HexColor('#FFD700')
        
        # ===== CERTIFICATE TITLE =====
        story.append(Paragraph("🏆", self.styles['CertificateTitle']))
        story.append(Paragraph("CERTIFICATE OF ACHIEVEMENT", self.styles['CertificateTitle']))
        story.append(Spacer(1, 20))
        
        # ===== DECORATIVE LINE =====
        story.append(HorizontalLine(400, colors.HexColor('#2E7D32'), 3))
        story.append(Spacer(1, 30))
        
        # ===== MAIN CONTENT =====
        content_style = ParagraphStyle(
            name='CertContent',
            parent=self.styles['ModernNormal'],
            fontName=FONT_REGULAR,
            fontSize=14,
            alignment=TA_CENTER,
            leading=24,
            textColor=colors.HexColor('#333333')
        )
        
        story.append(Paragraph("This certifies that", content_style))
        story.append(Spacer(1, 15))
        
        # Recipient name with fancy styling
        name_style = ParagraphStyle(
            name='CertName',
            parent=self.styles['ModernNormal'],
            fontName=FONT_BOLD,
            fontSize=32,
            alignment=TA_CENTER,
            leading=40,
            textColor=colors.HexColor('#2E7D32')
        )
        story.append(Paragraph(user_data['username'], name_style))
        story.append(Spacer(1, 15))
        
        story.append(Paragraph("has successfully completed the", content_style))
        story.append(Spacer(1, 5))
        
        # Assessment type
        type_style = ParagraphStyle(
            name='CertType',
            parent=self.styles['ModernNormal'],
            fontName=FONT_BOLD,
            fontSize=18,
            alignment=TA_CENTER,
            leading=24,
            textColor=colors.HexColor('#388E3C')
        )
        story.append(Paragraph(assessment_type, type_style))
        story.append(Spacer(1, 15))
        
        # Score
        score_style = ParagraphStyle(
            name='CertScore',
            parent=self.styles['ModernNormal'],
            fontName=FONT_BOLD,
            fontSize=24,
            alignment=TA_CENTER,
            leading=30,
            textColor=colors.HexColor('#FF9800')
        )
        story.append(Paragraph(f"Score: {score}/100", score_style))
        story.append(Spacer(1, 20))
        
        # Date
        date_style = ParagraphStyle(
            name='CertDate',
            parent=self.styles['ModernNormal'],
            fontName=FONT_REGULAR,
            fontSize=12,
            alignment=TA_CENTER,
            leading=16,
            textColor=colors.HexColor('#757575')
        )
        story.append(Paragraph(datetime.now().strftime('%B %d, %Y'), date_style))
        story.append(Spacer(1, 30))
        
        # ===== DECORATIVE LINE =====
        story.append(HorizontalLine(400, colors.HexColor('#2E7D32'), 2))
        story.append(Spacer(1, 20))
        
        # ===== SIGNATURES =====
        sig_data = [
            ['', ''],
            ['_________________________', '_________________________'],
            ['Authorized Signatory', 'Carbon ESG Platform']
        ]
        sig_table = Table(sig_data, colWidths=[250, 250])
        sig_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, -1), FONT_REGULAR),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#757575')),
        ]))
        story.append(sig_table)
        story.append(Spacer(1, 20))
        
        # ===== DISCLAIMER =====
        disclaimer_text = """
        <para alignment='center'>
        <font color='#9E9E9E' size='8'>
        This is a participation certificate for educational purposes. It is not a formal ESG certification.
        </font>
        </para>
        """
        story.append(Paragraph(disclaimer_text, self.styles['ModernSmall']))
        
        # Build PDF
        doc.build(story)
        return filename