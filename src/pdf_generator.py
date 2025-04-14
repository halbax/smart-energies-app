# src/pdf_generator.py

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet
from datetime import datetime
import os


def create_pdf(client_name, result, cal_price, q_price, m_price, spot_price, marze_fix, marze_spot, spot_avg, validity):
    filename = f"outputs/{client_name}_nabidka.pdf"
    doc = SimpleDocTemplate(filename, pagesize=A4)
    styles = getSampleStyleSheet()
    story = []

    # Logo
    logo_path = "assets/logo.jpg"
    if os.path.exists(logo_path):
        story.append(Image(logo_path, width=120, height=40))
    story.append(Spacer(1, 12))

    # Nadpis
    title = Paragraph(f"<b>Cenová nabídka pro: {client_name}</b>", styles['Title'])
    story.append(title)
    story.append(Spacer(1, 12))

    # Datum a platnost
    datum = datetime.now().strftime("%d.%m.%Y")
    info = Paragraph(f"Vygenerováno: {datum} | Platnost nabídky do: {validity}", styles['Normal'])
    story.append(info)
    story.append(Spacer(1, 12))

    # Tabulka s výsledky
    data = [["Produkt", "Objem [MWh]"]]
    for i, row in result['summary'].iterrows():
        data.append([row["Produkt"], f"{row['Objem [MWh]']:.2f}"])

    table = Table(data, colWidths=[100, 100])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.lightblue),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('GRID', (0, 0), (-1, -1), 1, colors.grey),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
    ]))
    story.append(table)
    story.append(Spacer(1, 24))

    # Kontakty
    kontakty = Paragraph("""
    <b>Kontakt:</b><br/>
    Smart Energies<br/>
    Tel: 606 240 891<br/>
    Email: info@smartenergies.cz<br/>
    Web: www.smartenergies.cz
    """, styles['Normal'])
    story.append(kontakty)
    story.append(Spacer(1, 12))

    # Poznámka o platnosti
    note = Paragraph("<i>Tato nabídka je platná do uvedeného data nebo do vyprodání kapacity obchodníka.</i>", styles['Italic'])
    story.append(note)

    # Uložení PDF
    doc.build(story)
    return filename