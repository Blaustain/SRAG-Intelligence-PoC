"""Camada de comentário: OpenAI opcional; fallback determinístico e rastreável."""
import os


def explain(metrics, news):
    key = os.getenv("OPENAI_API_KEY")
    if key:
        try:
            from openai import OpenAI
            client = OpenAI(api_key=key)
            prompt = ("Você é um assistente de vigilância epidemiológica. Comente os indicadores abaixo "
                      "sem diagnosticar, sem inventar causalidade e deixando explícitas as limitações. "
                      "Notícias são contexto secundário, não comprovam os números. Dados: "
                      f"{metrics}. Notícias: {news[:5]}")
            response = client.responses.create(model=os.getenv("OPENAI_MODEL", "gpt-4.1-mini"), input=prompt)
            return response.output_text
        except Exception as exc:
            return f"Não foi possível consultar o LLM ({type(exc).__name__}). " + fallback(metrics)
    return fallback(metrics)


def fallback(m):
    growth = m.get("growth_pct")
    if growth is None: trend = "Não há base comparativa suficiente para calcular a variação percentual."
    elif growth > 0: trend = f"Os registros do período aumentaram {growth:.1f}% em relação aos 30 dias anteriores."
    elif growth < 0: trend = f"Os registros do período diminuíram {abs(growth):.1f}% em relação aos 30 dias anteriores."
    else: trend = "O volume de registros permaneceu estável em relação aos 30 dias anteriores."
    return (trend + " A taxa de mortalidade considera somente registros com evolução conhecida. "
            "A proporção de UTI representa pacientes SRAG hospitalizados com UTI informada, não ocupação de leitos. "
            "A variável VACINA representa vacinação contra gripe informada entre os casos, não cobertura da população. "
            "Considere atraso de notificação, sub-registro e completude dos campos antes de tomar decisões.")
