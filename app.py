import datetime
import os
import streamlit as st
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from num2words import num2words

st.set_page_config(page_title="Rajesh Invoice Generator", page_icon="🧾", layout="centered")

# Function for 6-digit invoice number (XXDDMM)
def generate_invoice_number(current_date):
    date_str = current_date.strftime("%d%m")
    counter_file = "invoice_counter.txt"
    today_str = current_date.strftime("%Y-%m-%d")
    
    count = 1
    last_date = ""
    
    if os.path.exists(counter_file):
        with open(counter_file, "r") as f:
            lines = f.readlines()
            if len(lines) >= 2:
                last_date = lines[0].strip()
                try:
                    count = int(lines[1].strip())
                except ValueError:
                    count = 1
                    
    if last_date == today_str:
        count += 1
    else:
        count = 1
        last_date = today_str
        
    with open(counter_file, "w") as f:
        f.write(f"{last_date}\n{count}\n")
        
    xx = f"{count:02d}"
    invoice_no = f"{xx}{date_str}"
    return invoice_no

# Convert amount to Indian Rupees words
def amount_to_words(amount):
    try:
        words = num2words(amount, lang='en_IN').capitalize()
        return f"INR {words} Only"
    except Exception:
        return f"INR {amount} Only"

# Generate Exact Template PDF
def generate_pdf(invoice_data, filename="invoice.pdf"):
    doc = SimpleDocTemplate(filename, pagesize=letter, rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=40)
    story = []
    styles = getSampleStyleSheet()
    
    primary_color = colors.HexColor("#007acc")
    
    title_style = ParagraphStyle(
        'InvoiceTitle', parent=styles['Heading1'],
        fontName='Helvetica-Bold', fontSize=22,
        textColor=primary_color, spaceAfter=0
    )
    
    normal_style = ParagraphStyle(
        'InvoiceNormal', parent=styles['Normal'],
        fontName='Helvetica', fontSize=10,
        textColor=colors.HexColor("#333333")
    )
    
    right_style = ParagraphStyle(
        'InvoiceRight', parent=normal_style, alignment=2
    )

    # Header: RAJESH
    story.append(Paragraph("RAJESH", title_style))
    story.append(Paragraph("INVOICE", ParagraphStyle('InvLabel', parent=normal_style, fontName='Helvetica-Bold', fontSize=12, textColor=colors.gray)))
    story.append(Spacer(1, 5))
    story.append(Table([['']], colWidths=[530], rowHeights=[2], style=TableStyle([('BACKGROUND', (0,0), (-1,-1), primary_color)])))
    story.append(Spacer(1, 15))
    
    # Issued To & Invoice Details[cite: 8]
    party_text = f"<b>ISSUED TO:</b><br/>{invoice_data['party_name']}<br/>{invoice_data['party_address'].replace(chr(10), '<br/>')}<br/>Phone: {invoice_data['party_phone']}"
    meta_text = f"<b>Invoice No:</b> {invoice_data['inv_no']}<br/><b>Date:</b> {invoice_data['invoice_date']}"
    
    header_table = Table([[Paragraph(party_text, normal_style), Paragraph(meta_text, right_style)]], colWidths=[330, 200])
    header_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('LEFTPADDING', (0,0), (-1,-1), 0),
        ('RIGHTPADDING', (0,0), (-1,-1), 0),
    ]))
    story.append(header_table)
    story.append(Spacer(1, 20))
    
    # Items Table Header & Rows[cite: 8]
    table_data = [['DESCRIPTION', 'UNIT PRICE', 'QTY', 'TOTAL']]
    for item in invoice_data['items']:
        item_total = item['unit_price'] * item['qty']
        table_data.append([item['desc'], f"₹{item['unit_price']:,.2f}", str(item['qty']), f"₹{item_total:,.2f}"])
        
    item_table = Table(table_data, colWidths=[230, 100, 80, 120])
    
    ts = [
        ('BACKGROUND', (0,0), (-1,0), primary_color),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,0), 10),
        ('BOTTOMPADDING', (0,0), (-1,0), 8),
        ('TOPPADDING', (0,0), (-1,0), 8),
        ('ALIGN', (1,0), (-1,-1), 'RIGHT'),
        ('ALIGN', (2,0), (2,-1), 'CENTER'),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#dddddd")),
    ]
    # Add light background to alternate rows
    for i in range(1, len(table_data)):
        if i % 2 == 0:
            ts.append(('BACKGROUND', (0, i), (-1, i), colors.HexColor("#f9f9f9")))
        ts.append(('TOPPADDING', (0, i), (-1, i), 8))
        ts.append(('BOTTOMPADDING', (0, i), (-1, i), 8))
        
    item_table.setStyle(TableStyle(ts))
    story.append(item_table)
    story.append(Spacer(1, 20))
    
    # Rupee in Word & Total Section[cite: 8]
    words_text = f"<b>RUPEE IN WORD:</b><br/>{amount_to_words(invoice_data['grand_total'])}"
    total_text = f"<b>TOTAL: ₹{invoice_data['grand_total']:,.2f}</b>"
    
    bottom_table = Table([
        [Paragraph(words_text, normal_style), Paragraph(total_text, ParagraphStyle('Tot', parent=normal_style, fontName='Helvetica-Bold', fontSize=13, alignment=2))]
    ], colWidths=[330, 200])
    bottom_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('LEFTPADDING', (0,0), (-1,-1), 0),
        ('RIGHTPADDING', (0,0), (-1,-1), 0),
    ]))
    
    story.append(bottom_table)
    doc.build(story)

# Streamlit UI
st.title("🧾 Rajesh Invoice Generator (INR)")
st.write("Multiple items add karein aur exact template ke sath PDF download karein[cite: 8].")

with st.form("invoice_form"):
    st.subheader("1. Party Details")
    party_name = st.text_input("Party Name (Issued To)[cite: 8]")
    party_address = st.text_area("Party Address")
    party_phone = st.text_input("Party Phone Number")
    
    st.subheader("2. Invoice Date")
    invoice_date = st.date_input("Invoice Date[cite: 8]", value=datetime.date.today())
    
    st.subheader("3. Items (Multiple Products/Services)")
    st.write("Yahan aap apne items add kar sakte hain:")
    
    # Using data editor for multiple items
    import pandas as pd
    default_df = pd.DataFrame([
        {"Description": "Brand Advisory Services[cite: 8]", "Unit Price (₹)": 100.0, "Quantity": 1}
    ])
    
    edited_df = st.data_editor(default_df, num_rows="dynamic", use_container_width=True)
    
    submitted = st.form_submit_button("Generate Invoice PDF")

if submitted:
    if not party_name:
        st.error("Kripya Party ka naam darj karein!")
    else:
        inv_no = generate_invoice_number(invoice_date)
        
        items_list = []
        grand_total = 0.0
        for index, row in edited_df.iterrows():
            desc = str(row["Description"])
            u_price = float(row["Unit Price (₹)"])
            qty = int(row["Quantity"])
            items_list.append({"desc": desc, "unit_price": u_price, "qty": qty})
            grand_total += u_price * qty
            
        invoice_data = {
            "party_name": party_name,
            "party_address": party_address,
            "party_phone": party_phone,
            "inv_no": inv_no,
            "invoice_date": invoice_date.strftime('%d-%m-%Y'),
            "items": items_list,
            "grand_total": grand_total
        }
        
        pdf_filename = f"Invoice_{inv_no}.pdf"
        generate_pdf(invoice_data, pdf_filename)
        
        st.success(f"Invoice successfully generate ho gaya hai! Invoice No: **{inv_no}**")
        
        with open(pdf_filename, "rb") as pdf_file:
            st.download_button(
                label="📥 Download Invoice PDF (INR)",
                data=pdf_file,
                file_name=pdf_filename,
                mime="application/pdf"
            )