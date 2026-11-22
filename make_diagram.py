from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib import colors
from reportlab.pdfbase.pdfmetrics import stringWidth
from pathlib import Path
p=Path('docs/architecture.pdf')
c=canvas.Canvas(str(p), pagesize=landscape(A4))
W,H=landscape(A4)
navy=colors.HexColor('#102A43'); blue=colors.HexColor('#176B87'); pale=colors.HexColor('#EAF2F8'); gray=colors.HexColor('#52606D'); green=colors.HexColor('#D9F2E6'); orange=colors.HexColor('#FFF1D6')
c.setFillColor(navy); c.rect(0,H-78,W,78,fill=1,stroke=0)
c.setFillColor(colors.white); c.setFont('Helvetica-Bold',21); c.drawString(34,H-42,'SRAG Intelligence | Arquitetura conceitual da PoC')
c.setFont('Helvetica',9); c.drawString(34,H-60,'Fluxo de dados, ferramentas, LLM, persistência, fontes externas e controles transversais')

def box(x,y,w,h,title,body,fill=pale,stroke=blue):
    c.setFillColor(fill); c.setStrokeColor(stroke); c.roundRect(x,y,w,h,10,fill=1,stroke=1)
    c.setFillColor(navy); c.setFont('Helvetica-Bold',10); c.drawCentredString(x+w/2,y+h-18,title)
    c.setFillColor(gray); c.setFont('Helvetica',8)
    lines=body.split('\n')
    for i,line in enumerate(lines): c.drawCentredString(x+w/2,y+h-34-i*11,line)

def arrow(x1,y1,x2,y2,label=None):
    c.setStrokeColor(gray); c.setFillColor(gray); c.setLineWidth(1.4); c.line(x1,y1,x2,y2)
    import math
    a=math.atan2(y2-y1,x2-x1); L=7
    p1=(x2-L*math.cos(a-.45),y2-L*math.sin(a-.45)); p2=(x2-L*math.cos(a+.45),y2-L*math.sin(a+.45))
    path=c.beginPath(); path.moveTo(x2,y2); path.lineTo(*p1); path.lineTo(*p2); path.close()
    c.drawPath(path,fill=1,stroke=0)
    if label:
        c.setFont('Helvetica-Oblique',7); c.drawCentredString((x1+x2)/2,(y1+y2)/2+6,label)

# top line
box(310,465,220,58,'Especialista / profissional de saúde','Interface web Streamlit • filtros por UF e período',fill=green)
box(310,365,220,65,'Agente principal / orquestração','Fluxo controlado: consulta → validação → síntese')
arrow(420,465,420,430,'solicita análise')
# tool boxes
box(45,245,190,78,'Tool: métricas e dados','SQL/SQLite • indicadores Python\nSéries diárias e mensais')
box(325,245,190,78,'Tool: notícias','RSS Google News\nTítulos, fonte, data e URL')
box(605,245,190,78,'Tool: relatório e gráficos','Plotly / Streamlit\nPDF e visualização')
arrow(365,365,145,323,'consulta dados')
arrow(420,365,420,323,'pesquisa contexto')
arrow(475,365,700,323,'consolida')
# data source row
box(45,125,190,70,'Banco SQLite','Tabela agregável srag_cases\nÍndices por data e UF',fill=orange,stroke=colors.HexColor('#C28B26'))
box(325,125,190,70,'Fonte externa de notícias','RSS público do Google News\nConsulta no momento da execução',fill=orange,stroke=colors.HexColor('#C28B26'))
box(605,125,190,70,'Saída para especialista','KPIs + gráficos + comentário\nAvisos metodológicos',fill=green)
arrow(140,245,140,195,'SQL')
arrow(420,245,420,195,'RSS')
arrow(700,245,700,195,'apresenta')
# LLM
box(310,40,220,52,'LLM opcional (OpenAI)','Recebe somente métricas agregadas + manchetes',fill=colors.HexColor('#F0E8FF'),stroke=colors.HexColor('#7856A6'))
arrow(420,125,420,92,'síntese contextual')
# transverse controls
c.setStrokeColor(colors.HexColor('#8A9BA8')); c.setDash(4,3); c.roundRect(25,25,W-50,H-120,12,fill=0,stroke=1); c.setDash()
c.setFillColor(gray); c.setFont('Helvetica-Bold',8); c.drawString(38, H-103,'CONTROLES TRANSVERSAIS')
c.setFont('Helvetica',8); c.drawString(38, H-116,'Minimização de dados • LGPD • segredos em variáveis de ambiente • guardrails • logs JSONL • rastreabilidade de fontes • validação humana')
c.setFont('Helvetica-Oblique',7); c.drawRightString(W-30,12,'PoC: SQLite e fluxo de agente controlado; sem autonomia irrestrita nem decisão clínica automatizada.')
c.save()
