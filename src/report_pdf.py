from io import BytesIO
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle


def build_report(metrics, commentary, state="Brasil"):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=18*mm, leftMargin=18*mm,
                            topMargin=17*mm, bottomMargin=17*mm)
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name="Sub", parent=styles["Normal"], textColor=colors.HexColor('#52606D'), leading=15))
    story = [Paragraph("SRAG Intelligence — Relatório Epidemiológico", styles["Title"]),
             Paragraph(f"Recorte geográfico: {state} | Período: {metrics.get('period_start')} a {metrics.get('period_end')}", styles["Sub"]), Spacer(1, 8*mm)]
    def fmt(v): return "N/D" if v is None else f"{v:.1f}%"
    rows = [["Indicador", "Resultado"], ["Casos nos últimos 30 dias", str(metrics.get('cases', 0))],
            ["Variação vs. 30 dias anteriores", fmt(metrics.get('growth_pct'))],
            ["Mortalidade entre evoluções conhecidas", fmt(metrics.get('mortality_pct'))],
            ["Proporção de hospitalizados com UTI informada (proxy)", fmt(metrics.get('uti_share_pct'))],
            ["Vacinação contra gripe informada entre casos (proxy)", fmt(metrics.get('vaccinated_cases_pct'))]]
    table = Table(rows, colWidths=[112*mm, 55*mm])
    table.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#102A43')),
                               ('TEXTCOLOR',(0,0),(-1,0),colors.white),('FONTNAME',(0,0),(-1,0),'Helvetica-Bold'),
                               ('GRID',(0,0),(-1,-1),.4,colors.HexColor('#D5DEE7')),
                               ('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,colors.HexColor('#F3F7FA')]),
                               ('VALIGN',(0,0),(-1,-1),'MIDDLE'),('PADDING',(0,0),(-1,-1),7)]))
    story += [table, Spacer(1, 7*mm), Paragraph("Comentário analítico", styles["Heading2"]), Paragraph(commentary.replace('&','&amp;').replace('<','&lt;').replace('>','&gt;'), styles['BodyText']),
              Spacer(1, 6*mm), Paragraph("Notas metodológicas e limitações", styles["Heading2"]),
              Paragraph("A base SIVEP-Gripe não informa o total de leitos UTI disponíveis; portanto, a proporção UTI não equivale à ocupação real. A variável VACINA descreve vacinação contra gripe entre notificações e não representa cobertura da população. Mortalidade considera EVOLUCAO=2 ou 3 entre evoluções conhecidas. Os dados podem apresentar atraso, subnotificação e revisão. Este documento é apoio analítico e não substitui avaliação epidemiológica profissional.", styles['BodyText']),
              Spacer(1, 5*mm), Paragraph("Fonte: Open DATASUS / SIVEP-Gripe. PoC — SRAG Intelligence.", styles['Sub'])]
    doc.build(story)
    return buffer.getvalue()
