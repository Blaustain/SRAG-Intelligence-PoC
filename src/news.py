"""Busca de notícias via RSS público do Google News. Notícias são contexto, não evidência clínica."""
from urllib.parse import quote
import feedparser


def search_news(query="Síndrome Respiratória Aguda Grave SRAG Brasil", limit=8):
    url = "https://news.google.com/rss/search?q=" + quote(query) + "&hl=pt-BR&gl=BR&ceid=BR:pt-419"
    feed = feedparser.parse(url)
    items = []
    for entry in feed.entries[:limit]:
        items.append({"title": entry.get("title", "Sem título"),
                      "link": entry.get("link", ""),
                      "published": entry.get("published", "Data não informada"),
                      "source": entry.get("source", {}).get("title", "Fonte não identificada")})
    return items
