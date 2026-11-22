"""Orquestrador de PoC: chama ferramentas especializadas em sequência controlada."""
from src.metrics import calculate_metrics
from src.news import search_news
from src.assistant import explain
from src.audit import audit


def generate_analysis(dataframe, state="Brasil"):
    # Tool 1: métricas são calculadas por código determinístico, não pelo LLM.
    metrics = calculate_metrics(dataframe)
    # Tool 2: notícias são recuperadas de fonte externa; falha não interrompe KPIs.
    try:
        news = search_news()
        news_error = None
    except Exception as exc:
        news, news_error = [], type(exc).__name__
    # Tool 3: LLM/fallback recebe apenas agregados e manchetes.
    commentary = explain(metrics, news)
    audit("orchestrated_report", {"state": state, "records": len(dataframe),
                                  "news_count": len(news), "news_error": news_error,
                                  "llm_enabled": bool(__import__('os').getenv('OPENAI_API_KEY'))})
    return {"metrics": metrics, "news": news, "commentary": commentary, "news_error": news_error}
