import io
from datetime import datetime
from decimal import Decimal
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, KeepTogether
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from app.models.billing import Invoice
from app.models.commercial import Quotation, QuotationVersion

class PDFService:
    @staticmethod
    def _create_styles():
        styles = getSampleStyleSheet()
        
        title_style = ParagraphStyle(
            'DocTitle',
            parent=styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=20,
            leading=24,
            textColor=colors.HexColor('#0f172a')
        )
        subtitle_style = ParagraphStyle(
            'DocSubtitle',
            parent=styles['Normal'],
            fontName='Helvetica',
            fontSize=10,
            leading=14,
            textColor=colors.HexColor('#64748b')
        )
        section_heading = ParagraphStyle(
            'SectionHeading',
            parent=styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=11,
            leading=15,
            textColor=colors.HexColor('#1e293b')
        )
        body_style = ParagraphStyle(
            'DocBody',
            parent=styles['Normal'],
            fontName='Helvetica',
            fontSize=9,
            leading=13,
            textColor=colors.HexColor('#334155')
        )
        body_bold = ParagraphStyle(
            'DocBodyBold',
            parent=styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=9,
            leading=13,
            textColor=colors.HexColor('#0f172a')
        )
        table_cell = ParagraphStyle(
            'TableCell',
            parent=styles['Normal'],
            fontName='Helvetica',
            fontSize=8,
            leading=11,
            textColor=colors.HexColor('#1e293b')
        )
        table_cell_bold = ParagraphStyle(
            'TableCellBold',
            parent=styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=8,
            leading=11,
            textColor=colors.HexColor('#0f172a')
        )
        table_cell_right = ParagraphStyle(
            'TableCellRight',
            parent=styles['Normal'],
            fontName='Helvetica',
            fontSize=8,
            leading=11,
            alignment=2,
            textColor=colors.HexColor('#1e293b')
        )
        table_cell_right_bold = ParagraphStyle(
            'TableCellRightBold',
            parent=styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=8,
            leading=11,
            alignment=2,
            textColor=colors.HexColor('#0f172a')
        )

        return {
            'title': title_style,
            'subtitle': subtitle_style,
            'heading': section_heading,
            'body': body_style,
            'body_bold': body_bold,
            'cell': table_cell,
            'cell_bold': table_cell_bold,
            'cell_right': table_cell_right,
            'cell_right_bold': table_cell_right_bold
        }

    @classmethod
    def generate_invoice_pdf(cls, invoice: Invoice) -> bytes:
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            leftMargin=36,
            rightMargin=36,
            topMargin=36,
            bottomMargin=36
        )

        st = cls._create_styles()
        elements = []

        # Header: Company Info and Invoice Title
        header_data = [
            [
                Paragraph("<b>BRIGHTLOOP SOFTWARE</b><br/>Subscription Management System<br/>GSTIN: 29AABCB1234F1Z5<br/>support@brightloop.com", st['body']),
                Paragraph(f"<b>TAX INVOICE</b><br/><font size=12 color='#2563eb'><b>{invoice.invoice_number}</b></font><br/>Status: {invoice.status.upper()}", st['cell_right'])
            ]
        ]
        header_table = Table(header_data, colWidths=[320, 220])
        header_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
        ]))
        elements.append(header_table)
        elements.append(Spacer(1, 10))

        # Bill To & Invoice Meta
        issue_str = invoice.issue_date.strftime("%d %b %Y") if invoice.issue_date else "N/A"
        due_str = invoice.due_date.strftime("%d %b %Y") if invoice.due_date else "N/A"
        business_name = invoice.business.company_name if invoice.business else "Customer Business"
        tax_id = getattr(invoice.business, "tax_id", None) or "Unregistered"
        address = invoice.business.billing_address or "Not Provided" if invoice.business else "N/A"

        meta_data = [
            [
                Paragraph("<b>BILLED TO:</b>", st['heading']),
                Paragraph("<b>INVOICE DETAILS:</b>", st['heading'])
            ],
            [
                Paragraph(f"<b>{business_name}</b><br/>Tax ID / GSTIN: {tax_id}<br/>Address: {address}", st['body']),
                Paragraph(f"<b>Issue Date:</b> {issue_str}<br/><b>Due Date:</b> {due_str}<br/><b>Billing Period:</b> {invoice.billing_period}<br/><b>Payment Terms:</b> {invoice.payment_terms}", st['body'])
            ]
        ]
        meta_table = Table(meta_data, colWidths=[320, 220])
        meta_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LINEBELOW', (0, 0), (-1, 0), 1, colors.HexColor('#cbd5e1')),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 1), (-1, 1), 6),
        ]))
        elements.append(meta_table)
        elements.append(Spacer(1, 15))

        # Line Items Table
        line_data = [
            [
                Paragraph("<b>Description</b>", st['cell_bold']),
                Paragraph("<b>Plan / Period</b>", st['cell_bold']),
                Paragraph("<b>Qty</b>", st['cell_right_bold']),
                Paragraph("<b>Unit Price (₹)</b>", st['cell_right_bold']),
                Paragraph("<b>Tax (₹)</b>", st['cell_right_bold']),
                Paragraph("<b>Total (₹)</b>", st['cell_right_bold'])
            ]
        ]

        for line in invoice.lines:
            desc = line.description or (line.product.name if line.product else "Service Item")
            plan_name = line.plan.name if line.plan else "Standard"
            line_data.append([
                Paragraph(desc, st['cell']),
                Paragraph(plan_name, st['cell']),
                Paragraph(str(line.quantity), st['cell_right']),
                Paragraph(f"{line.unit_price:,.2f}", st['cell_right']),
                Paragraph(f"{line.tax_amount:,.2f} ({line.tax_rate_percent}%)", st['cell_right']),
                Paragraph(f"{line.line_total:,.2f}", st['cell_right'])
            ])

        line_table = Table(line_data, colWidths=[170, 90, 40, 80, 80, 80])
        line_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f1f5f9')),
            ('ALIGN', (2, 0), (-1, -1), 'RIGHT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
            ('LINEBELOW', (0, 0), (-1, 0), 1.5, colors.HexColor('#94a3b8')),
            ('LINEBELOW', (0, 1), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
        ]))
        elements.append(line_table)
        elements.append(Spacer(1, 12))

        # Summary Totals
        summary_data = [
            [Paragraph("Subtotal:", st['cell_bold']), Paragraph(f"₹ {invoice.subtotal:,.2f}", st['cell_right'])],
            [Paragraph("Discount:", st['cell_bold']), Paragraph(f"- ₹ {invoice.discount_total:,.2f}", st['cell_right'])],
            [Paragraph("Taxes (GST):", st['cell_bold']), Paragraph(f"₹ {invoice.tax_total:,.2f}", st['cell_right'])],
            [Paragraph("<b>Final Total:</b>", st['heading']), Paragraph(f"<b>₹ {invoice.final_total:,.2f}</b>", st['cell_right_bold'])],
            [Paragraph("Amount Paid:", st['cell_bold']), Paragraph(f"₹ {invoice.amount_paid:,.2f}", st['cell_right'])],
            [Paragraph("<b>Balance Due:</b>", st['heading']), Paragraph(f"<b>₹ {invoice.remaining_balance:,.2f}</b>", st['cell_right_bold'])]
        ]
        summary_table = Table(summary_data, colWidths=[140, 100])
        summary_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 3),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
            ('LINEBELOW', (0, 3), (-1, 3), 1, colors.HexColor('#cbd5e1')),
            ('LINEBELOW', (0, -1), (-1, -1), 1.5, colors.HexColor('#0f172a')),
            ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#f8fafc')),
        ]))

        # Align Summary to the right
        layout_data = [
            [
                Paragraph("<b>Payment Instructions:</b><br/>Bank: HDFC Bank<br/>Account: 50200012345678<br/>IFSC: HDFC0000123<br/>Branch: Indiranagar, Bangalore<br/>Please quote invoice number in payment reference.", st['body']),
                summary_table
            ]
        ]
        layout_table = Table(layout_data, colWidths=[300, 240])
        layout_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ]))
        elements.append(KeepTogether(layout_table))

        # Footer notes
        elements.append(Spacer(1, 20))
        elements.append(Paragraph("This is a computer generated invoice and requires no physical signature.", st['subtitle']))

        doc.build(elements)
        buffer.seek(0)
        return buffer.getvalue()

    @classmethod
    def generate_quotation_pdf(cls, quotation: Quotation, version: QuotationVersion) -> bytes:
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            leftMargin=36,
            rightMargin=36,
            topMargin=36,
            bottomMargin=36
        )

        st = cls._create_styles()
        elements = []

        # Header
        header_data = [
            [
                Paragraph("<b>BRIGHTLOOP SOFTWARE</b><br/>Subscription Management System<br/>GSTIN: 29AABCB1234F1Z5<br/>sales@brightloop.com", st['body']),
                Paragraph(f"<b>COMMERCIAL QUOTATION</b><br/><font size=12 color='#2563eb'><b>{quotation.quotation_number} (v{version.version_number})</b></font><br/>Status: {version.status.upper()}", st['cell_right'])
            ]
        ]
        header_table = Table(header_data, colWidths=[320, 220])
        header_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
        ]))
        elements.append(header_table)
        elements.append(Spacer(1, 10))

        # Details
        created_str = version.created_at.strftime("%d %b %Y") if version.created_at else "N/A"
        valid_str = version.valid_until.strftime("%d %b %Y") if version.valid_until else "30 Days from Issue"
        business_name = quotation.business.company_name if quotation.business else "Prospective Client"
        tax_id = getattr(quotation.business, "tax_id", None) or "Unregistered"

        meta_data = [
            [
                Paragraph("<b>PREPARED FOR:</b>", st['heading']),
                Paragraph("<b>PROPOSAL DETAILS:</b>", st['heading'])
            ],
            [
                Paragraph(f"<b>{business_name}</b><br/>Tax ID / GSTIN: {tax_id}", st['body']),
                Paragraph(f"<b>Date:</b> {created_str}<br/><b>Valid Until:</b> {valid_str}<br/><b>Payment Terms:</b> {version.payment_terms}", st['body'])
            ]
        ]
        meta_table = Table(meta_data, colWidths=[320, 220])
        meta_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LINEBELOW', (0, 0), (-1, 0), 1, colors.HexColor('#cbd5e1')),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 1), (-1, 1), 6),
        ]))
        elements.append(meta_table)
        elements.append(Spacer(1, 15))

        # Line Items
        line_data = [
            [
                Paragraph("<b>Item Description</b>", st['cell_bold']),
                Paragraph("<b>Plan</b>", st['cell_bold']),
                Paragraph("<b>Seats / Qty</b>", st['cell_right_bold']),
                Paragraph("<b>Unit Price (₹)</b>", st['cell_right_bold']),
                Paragraph("<b>Discount (₹)</b>", st['cell_right_bold']),
                Paragraph("<b>Net Total (₹)</b>", st['cell_right_bold'])
            ]
        ]

        for line in version.lines:
            desc = line.description or (line.product.name if line.product else "Software License")
            plan_name = line.plan.name if line.plan else "Standard"
            line_data.append([
                Paragraph(desc, st['cell']),
                Paragraph(plan_name, st['cell']),
                Paragraph(str(line.quantity), st['cell_right']),
                Paragraph(f"{line.unit_price:,.2f}", st['cell_right']),
                Paragraph(f"{line.discount_amount:,.2f} ({line.discount_percent}%)", st['cell_right']),
                Paragraph(f"{line.line_total:,.2f}", st['cell_right'])
            ])

        line_table = Table(line_data, colWidths=[170, 90, 50, 75, 75, 80])
        line_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f1f5f9')),
            ('ALIGN', (2, 0), (-1, -1), 'RIGHT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
            ('LINEBELOW', (0, 0), (-1, 0), 1.5, colors.HexColor('#94a3b8')),
            ('LINEBELOW', (0, 1), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
        ]))
        elements.append(line_table)
        elements.append(Spacer(1, 12))

        # Summary
        summary_data = [
            [Paragraph("Subtotal:", st['cell_bold']), Paragraph(f"₹ {version.subtotal:,.2f}", st['cell_right'])],
            [Paragraph("Total Discount:", st['cell_bold']), Paragraph(f"- ₹ {version.discount_total:,.2f}", st['cell_right'])],
            [Paragraph("Estimated Taxes:", st['cell_bold']), Paragraph(f"₹ {version.tax_total:,.2f}", st['cell_right'])],
            [Paragraph("<b>Final Quoted Total:</b>", st['heading']), Paragraph(f"<b>₹ {version.final_total:,.2f}</b>", st['cell_right_bold'])],
        ]
        summary_table = Table(summary_data, colWidths=[140, 100])
        summary_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 3),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
            ('LINEBELOW', (0, -1), (-1, -1), 1.5, colors.HexColor('#0f172a')),
            ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#f8fafc')),
        ]))

        layout_data = [
            [
                Paragraph("<b>Terms & Acceptance:</b><br/>1. Acceptance of this quotation forms a binding commercial agreement.<br/>2. Invoicing will proceed upon formal acceptance in the Customer Portal.<br/>3. Payment terms as stated above apply from invoice date.", st['body']),
                summary_table
            ]
        ]
        layout_table = Table(layout_data, colWidths=[300, 240])
        layout_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ]))
        elements.append(KeepTogether(layout_table))

        elements.append(Spacer(1, 20))
        elements.append(Paragraph("Generated by Brightloop Subscription Management System.", st['subtitle']))

        doc.build(elements)
        buffer.seek(0)
        return buffer.getvalue()
