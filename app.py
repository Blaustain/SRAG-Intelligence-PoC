import os, sys
from pathlib import Path
import streamlit as st
import pandas as pd

ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT))
from src.data_pipeline import load_srag
from src.database import build_database, query_cases
from src.metrics import calculate_metrics, daily_series, monthly_series
from src.orchestrator import generate_analysis
from src.report_pdf import build_report
from src.audit import audit

st.set_page_config(page_title="SRAG Intelligence", page_icon="🫁", layout="wide")
st.markdown("""
<style>
.block-container{padding-top:1.5rem;max-width:1500px}
[data-testid="stMetric"]{background:#f4f7fb;padding:16px;border-radius:12px;border:1px solid #e5eaf1}
.hero{padding:22px 26px;border-radius:16px;background:linear-gradient(110deg,#10243a,#176b87);color:white;margin-bottom:18px}
.hero h1{color:white;margin:0}.hero p{color:#d9eaf2;margin:6px 0 0}
.small-note{font-size:0.86rem;color:#687385}

/* Cards dos indicadores */
[data-testid="stMetric"] {
    background-color: #FFFFFF !important;
    border: 1px solid #DCE3EB !important;
    border-radius: 12px !important;
    padding: 20px !important;
    box-shadow: 0 3px 10px rgba(0,0,0,0.12);
}

/* Títulos dos indicadores */
[data-testid="stMetricLabel"] {
    color: #334155 !important;
    font-weight: 600 !important;
    font-size: 14px !important;
}

/* Valores dos indicadores */
[data-testid="stMetricValue"] {
    color: #0F2942 !important;
    font-size: 32px !important;
    font-weight: 700 !important;
}

/* Texto auxiliar */
[data-testid="stMetricDelta"] {
    color: #166534 !important;
}

/* Texto dentro dos cards */
[data-testid="stMetric"] p {
    color: #334155 !important;
}

/* Ajuste dos títulos da aplicação */
h1, h2, h3 {
    color: #F8FAFC !important;
}

</style>
<div class="hero"><h1>🫁 SRAG Intelligence</h1><p>Monitoramento epidemiológico, indicadores auditáveis e contexto de notícias para especialistas.</p></div>
""", unsafe_allow_html=True)

DATA_PATH = Path(os.getenv("SRAG_DATA_PATH", ROOT / "data/raw/INFLUD25_DATASUS-Versao26-06-2025.zip"))

@st.cache_data(show_spinner="Carregando e tratando a base pública do SIVEP-Gripe...")
def get_data(path, mtime):
    return load_srag(path)

with st.sidebar:
    st.header("Configurações")
    st.caption("Fonte: Open DATASUS / SIVEP-Gripe")
    st.write(f"Arquivo: `{DATA_PATH.name}`")
    if st.button("Recarregar dados"):
        get_data.clear(); st.rerun()
    st.divider()
    st.markdown("**Escopo geográfico**")

try:
    if not DATA_PATH.exists():
        st.error("Base não encontrada. Coloque o ZIP em data/raw ou configure SRAG_DATA_PATH.")
        st.stop()
    df = get_data(str(DATA_PATH), DATA_PATH.stat().st_mtime)
    db_path = ROOT / "data/processed/srag.sqlite"
    db_path.parent.mkdir(parents=True, exist_ok=True)
    if not db_path.exists() or db_path.stat().st_mtime < DATA_PATH.stat().st_mtime:
        build_database(df, db_path)
    df = query_cases(db_path)
except Exception as e:
    st.exception(e); st.stop()

max_date = df.DT_SIN_PRI.max().normalize()
min_date = df.DT_SIN_PRI.min().normalize()
with st.sidebar:
    states = sorted([x for x in df.get("SG_UF", pd.Series(dtype=str)).dropna().unique() if str(x).strip()])
    selected_state = st.selectbox("UF de residência", ["Brasil"] + states)
    st.caption(f"Período disponível na base: {min_date:%d/%m/%Y} a {max_date:%d/%m/%Y}")

view = df if selected_state == "Brasil" else df[df.SG_UF.eq(selected_state)]
metrics = calculate_metrics(view)
audit("dashboard_view", {"state": selected_state, "data_max": str(max_date), "rows": len(view)})

st.subheader("Visão geral")
st.caption(f"Indicadores calculados para os 30 dias terminados em {metrics['period_end']}. A data final acompanha a última data de sintomas existente na base, não a data de hoje.")
c1,c2,c3,c4 = st.columns(4)
c1.metric("Casos nos últimos 30 dias", f"{metrics['cases']:,}".replace(",","."))
c2.metric("Variação vs. 30 dias anteriores", "N/D" if metrics['growth_pct'] is None else f"{metrics['growth_pct']:+.1f}%")
c3.metric("Mortalidade entre evoluções conhecidas", "N/D" if metrics['mortality_pct'] is None else f"{metrics['mortality_pct']:.1f}%")
c4.metric("Casos hospitalizados com UTI", "N/D" if metrics['uti_share_pct'] is None else f"{metrics['uti_share_pct']:.1f}%")

c5,c6 = st.columns(2)
c5.metric("Casos com vacinação contra gripe informada", "N/D" if metrics['vaccinated_cases_pct'] is None else f"{metrics['vaccinated_cases_pct']:.1f}%")
c6.metric("Registros na base filtrada", f"{len(view):,}".replace(",","."))

st.warning("**Interpretação obrigatória:** a base SRAG não informa o total de leitos de UTI disponíveis nem a população elegível/vacinada. Portanto, o indicador de UTI exibido é a proporção de hospitalizados com UTI registrada (proxy), e vacinação é a proporção de casos com vacinação contra gripe informada. Não são, respectivamente, ocupação real de leitos nem cobertura vacinal populacional.")

left,right = st.columns(2)
with left:
    st.subheader("Casos por dia — últimos 30 dias")
    d = daily_series(view)
    st.line_chart(d.set_index("date")["cases"], use_container_width=True)
with right:
    st.subheader("Casos por mês — últimos 12 meses")
    m = monthly_series(view)
    st.bar_chart(m.set_index("month")["cases"], use_container_width=True)

st.divider()
st.subheader("Análise assistida por IA")
if st.button("Gerar comentário epidemiológico", type="primary"):
    with st.spinner("Consultando ferramentas e consolidando a análise..."):
        analysis = generate_analysis(view, selected_state)
        news = analysis["news"]
        commentary = analysis["commentary"]
    st.markdown(commentary)
    st.caption("O comentário é apoio à análise, não substitui a avaliação epidemiológica profissional.")
    pdf_bytes = build_report(metrics, commentary, selected_state)
    st.download_button("Baixar relatório em PDF", data=pdf_bytes, file_name="relatorio_srag_intelligence.pdf", mime="application/pdf")
    with st.expander(f"Notícias encontradas ({len(news)})"):
        if news:
            for n in news:
                st.markdown(f"**[{n['title']}]({n['link']})**  \n{n['source']} · {n['published']}")
        else: st.write("Nenhuma notícia retornada nesta consulta.")
else:
    st.info("Clique em 'Gerar comentário epidemiológico' para buscar notícias atuais e produzir uma síntese contextual. Sem chave de LLM, a aplicação utiliza comentários determinísticos e transparentes.")

with st.expander("Metodologia, definições e limitações"):
    st.markdown("""
    - **Casos:** registros com data de primeiros sintomas (`DT_SIN_PRI`) dentro da janela.
    - **Aumento:** (casos nos 30 dias atuais − casos nos 30 dias anteriores) / casos nos 30 dias anteriores × 100.
    - **Mortalidade:** óbitos registrados (`EVOLUCAO` 2 ou 3) / registros com evolução conhecida (1, 2 ou 3) × 100. Confirmar códigos no dicionário da versão utilizada.
    - **UTI (proxy):** registros com `UTI=1` / registros hospitalizados com `UTI` conhecida (1 ou 2) × 100.
    - **Vacinação entre casos:** `VACINA=1` / registros com `VACINA` conhecida (1 ou 2) × 100.
    - **Qualidade:** datas inválidas e ausentes são descartadas da série; identificadores são usados apenas para deduplicação e não são exibidos.
    - **Defasagem:** dados de vigilância podem sofrer atraso, revisão e subnotificação. A data máxima do conjunto deve ser observada antes de interpretar tendência recente.
    - **Privacidade:** o pipeline seleciona somente colunas agregáveis e exclui nome, CPF, CNS, endereço, telefone e demais identificadores diretos.
    """)

st.caption("SRAG Intelligence · PoC educacional/analítica · Não é sistema de diagnóstico ou decisão clínica.")
