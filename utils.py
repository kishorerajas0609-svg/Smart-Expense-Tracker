import csv
import io
from decimal import Decimal
from django.http import HttpResponse
from django.utils import timezone
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfgen import canvas


# Smart Category Keyword Rules
CATEGORY_KEYWORDS = {
    'Travel': [
        'uber', 'ola', 'lyft', 'bus', 'train', 'metro', 'flight', 'airline',
        'petrol', 'diesel', 'fuel', 'gas station', 'toll', 'parking', 'taxi',
        'cab', 'transit', 'auto', 'commute', 'railway', 'fare', 'subway'
    ],
    'Food': [
        'pizza', 'burger', 'restaurant', 'cafe', 'coffee', 'groceries',
        'grocery', 'supermarket', 'lunch', 'dinner', 'breakfast', 'meal',
        'snack', 'snacks', 'starbucks', 'mcdonald', 'kfc', 'domino', 'swiggy',
        'zomato', 'foodpanda', 'doordash', 'dining', 'food', 'bakery', 'tea',
        'juice', 'bread', 'milk', 'vegetables', 'fruits', 'diner'
    ],
    'Bills': [
        'electricity', 'water', 'internet', 'wifi', 'phone', 'mobile', 'rent',
        'gas', 'utility', 'utilities', 'bills', 'bill', 'recharge', 'broadband',
        'maintenance', 'landline', 'dth', 'cylinder', 'sewer', 'trash'
    ],
    'Entertainment': [
        'movie', 'cinema', 'games', 'gaming', 'netflix', 'spotify', 'hulu',
        'disney', 'prime video', 'party', 'club', 'concert', 'theater',
        'amusement', 'outing', 'pub', 'entertainment', 'steam', 'playstation',
        'xbox', 'music', 'ticket', 'show', 'bowling'
    ],
    'Healthcare': [
        'doctor', 'medicine', 'pharmacy', 'hospital', 'clinic', 'dental',
        'dentist', 'medical', 'health', 'tablet', 'tablets', 'pills', 'syrup',
        'prescription', 'checkup', 'lab test', 'blood test', 'optical',
        'glasses', 'therapy', 'vaccine', 'physio'
    ],
    'Education': [
        'books', 'book', 'tuition', 'courses', 'course', 'class', 'classes',
        'udemy', 'coursera', 'edx', 'college', 'school', 'fee', 'fees',
        'exam', 'university', 'stationery', 'textbook', 'training', 'tutor',
        'academy', 'seminar', 'workshop'
    ],
    'Shopping': [
        'amazon', 'flipkart', 'clothes', 'clothing', 'shoes', 'dress', 'shirt',
        'shopping', 'mall', 'zara', 'h&m', 'electronics', 'gadget', 'accessory',
        'accessories', 'cosmetics', 'perfume', 'watch', 'boots', 'jacket',
        'myntra', 'ebay', 'walmart', 'target'
    ],
}


def predict_category(text):
    """Predict category based on keywords found in the text."""
    if not text:
        return 'Other'
    
    text_lower = text.lower()
    for category, keywords in CATEGORY_KEYWORDS.items():
        for kw in keywords:
            # Word boundary matching or substring matching
            if kw in text_lower:
                return category
    return 'Other'


class NumberedCanvas(canvas.Canvas):
    """Two-pass canvas for dynamic total page count."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_number(num_pages)
            super().showPage()
        super().save()

    def draw_page_number(self, page_count):
        self.saveState()
        self.setFont("Helvetica", 9)
        self.setFillColor(colors.HexColor("#64748B"))
        # Footer text
        text = f"Smart Expense Tracker  |  Page {self._pageNumber} of {page_count}"
        self.drawRightString(letter[0] - 36, 25, text)
        self.drawString(36, 25, "Confidential - For personal finance use only")
        self.setStrokeColor(colors.HexColor("#E2E8F0"))
        self.setLineWidth(0.5)
        self.line(36, 38, letter[0] - 36, 38)
        self.restoreState()


def generate_expense_csv(user, expenses, filter_info="All Time"):
    """Generate CSV file containing user expenses."""
    response = HttpResponse(content_type='text/csv; charset=utf-8')
    response.write('\ufeff')  # UTF-8 BOM so Excel opens Indian Rupee symbol correctly
    timestamp = timezone.now().strftime("%Y%m%d_%H%M%S")
    response['Content-Disposition'] = f'attachment; filename="smart_expenses_{user.username}_{timestamp}.csv"'

    writer = csv.writer(response)
    # Header metadata
    writer.writerow(["Smart Expense Tracker - Personal Expense Report"])
    writer.writerow(["User", user.username])
    writer.writerow(["Currency", "Indian Rupee (INR / ₹)"])
    writer.writerow(["Generated At", timezone.now().strftime("%Y-%m-%d %H:%M:%S")])
    writer.writerow(["Filter Range", filter_info])
    writer.writerow([])
    
    # Table headers
    writer.writerow(["ID", "Date", "Description", "Category", "Amount (₹)", "Notes", "Logged At"])

    total_amount = Decimal('0.00')
    for exp in expenses:
        total_amount += exp.amount
        writer.writerow([
            exp.id,
            exp.date.strftime("%Y-%m-%d"),
            exp.description,
            exp.category,
            f"₹{exp.amount:.2f}",
            exp.notes or "",
            exp.created_at.strftime("%Y-%m-%d %H:%M")
        ])

    writer.writerow([])
    writer.writerow(["", "", "Total Transactions:", len(expenses), f"₹{total_amount:.2f}", "", ""])

    return response


def generate_expense_pdf(user, expenses, filter_info="All Time"):
    """Generate professional PDF expense report using ReportLab."""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        leftMargin=36,
        rightMargin=36,
        topMargin=36,
        bottomMargin=48
    )

    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=20,
        leading=24,
        textColor=colors.HexColor('#0F172A'),
        spaceAfter=4
    )
    subtitle_style = ParagraphStyle(
        'DocSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10,
        leading=14,
        textColor=colors.HexColor('#475569')
    )
    metric_title_style = ParagraphStyle(
        'MetricTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=9,
        leading=11,
        textColor=colors.HexColor('#64748B')
    )
    metric_val_style = ParagraphStyle(
        'MetricValue',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=14,
        leading=17,
        textColor=colors.HexColor('#0F172A')
    )
    table_cell_style = ParagraphStyle(
        'TableCell',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=12,
        textColor=colors.HexColor('#1E293B')
    )
    table_head_style = ParagraphStyle(
        'TableHead',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=9,
        leading=12,
        textColor=colors.white
    )

    elements = []

    # Title & Header
    elements.append(Paragraph("Smart Expense Tracker", title_style))
    gen_time = timezone.now().strftime("%B %d, %Y %I:%M %p")
    elements.append(Paragraph(f"Financial Expense Statement &bull; Generated for <b>{user.username}</b> ({user.email or 'No email'}) on {gen_time}", subtitle_style))
    elements.append(Paragraph(f"Filter / Range: <b>{filter_info}</b>", subtitle_style))
    elements.append(Spacer(1, 12))

    # Calculate metrics
    total_spent = sum((e.amount for e in expenses), Decimal('0.00'))
    total_count = len(expenses)
    avg_spent = (total_spent / total_count) if total_count > 0 else Decimal('0.00')

    # Summary Cards Table
    summary_data = [
        [
            Paragraph("TOTAL EXPENDITURE", metric_title_style),
            Paragraph("TRANSACTION COUNT", metric_title_style),
            Paragraph("AVERAGE TICKET", metric_title_style)
        ],
        [
            Paragraph(f"₹{total_spent:,.2f}", metric_val_style),
            Paragraph(f"{total_count:,}", metric_val_style),
            Paragraph(f"₹{avg_spent:,.2f}", metric_val_style)
        ]
    ]
    summary_table = Table(summary_data, colWidths=[180, 180, 180])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#F8FAFC')),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#E2E8F0')),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E2E8F0')),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('LEFTPADDING', (0, 0), (-1, -1), 12),
        ('RIGHTPADDING', (0, 0), (-1, -1), 12),
    ]))
    elements.append(summary_table)
    elements.append(Spacer(1, 16))

    # Category breakdown table
    cat_totals = {}
    for exp in expenses:
        cat_totals[exp.category] = cat_totals.get(exp.category, Decimal('0.00')) + exp.amount

    if cat_totals:
        elements.append(Paragraph("<b>Category Spending Summary</b>", styles['Heading3']))
        cat_rows = [[
            Paragraph("Category", table_head_style),
            Paragraph("Amount (₹)", table_head_style),
            Paragraph("Share of Total", table_head_style)
        ]]
        for cat, amt in sorted(cat_totals.items(), key=lambda x: x[1], reverse=True):
            pct = (amt / total_spent * 100) if total_spent > 0 else 0
            cat_rows.append([
                Paragraph(cat, table_cell_style),
                Paragraph(f"₹{amt:,.2f}", table_cell_style),
                Paragraph(f"{pct:.1f}%", table_cell_style)
            ])
        cat_table = Table(cat_rows, colWidths=[200, 170, 170])
        cat_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3B82F6')),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F1F5F9')]),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#CBD5E1')),
            ('TOPPADDING', (0, 0), (-1, -1), 5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
            ('LEFTPADDING', (0, 0), (-1, -1), 8),
            ('RIGHTPADDING', (0, 0), (-1, -1), 8),
        ]))
        elements.append(cat_table)
        elements.append(Spacer(1, 16))

    # Transaction Records Table
    elements.append(Paragraph("<b>Expense Transaction Records</b>", styles['Heading3']))
    
    trans_rows = [[
        Paragraph("Date", table_head_style),
        Paragraph("Description", table_head_style),
        Paragraph("Category", table_head_style),
        Paragraph("Amount (₹)", table_head_style),
        Paragraph("Notes", table_head_style),
    ]]

    for exp in expenses:
        trans_rows.append([
            Paragraph(exp.date.strftime("%Y-%m-%d"), table_cell_style),
            Paragraph(exp.description, table_cell_style),
            Paragraph(exp.category, table_cell_style),
            Paragraph(f"₹{exp.amount:,.2f}", table_cell_style),
            Paragraph(exp.notes or "-", table_cell_style),
        ])

    if not expenses:
        trans_rows.append([
            Paragraph("-", table_cell_style),
            Paragraph("No expense records found matching criteria.", table_cell_style),
            Paragraph("-", table_cell_style),
            Paragraph("₹0.00", table_cell_style),
            Paragraph("-", table_cell_style),
        ])

    trans_table = Table(trans_rows, colWidths=[70, 180, 110, 80, 100], repeatRows=1)
    trans_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1E293B')),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F8FAFC')]),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E2E8F0')),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
    ]))
    elements.append(trans_table)

    # Build PDF with dynamic page numbering
    doc.build(elements, canvasmaker=NumberedCanvas)
    buffer.seek(0)

    timestamp = timezone.now().strftime("%Y%m%d_%H%M%S")
    response = HttpResponse(buffer.getvalue(), content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="smart_expenses_{user.username}_{timestamp}.pdf"'
    return response
