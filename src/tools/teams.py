import json, requests
from typing import Optional
from ..settings import settings

def post_to_teams(text: str, title: Optional[str] = None) -> bool:
    """
    Odošle jednoduchú kartu do MS Teams cez Incoming Webhook.
    Nastav v kanáli Connectors -> Incoming Webhook a vlož URL do TEAMS_WEBHOOK_URL.
    """
    if not settings.teams_webhook_url:
        return False
    payload = {
        "@type": "MessageCard",
        "@context": "http://schema.org/extensions",
        "summary": title or "MerakiOps Agent",
        "themeColor": "0076D7",
        "title": title or "MerakiOps Agent",
        "text": text,
    }
    r = requests.post(settings.teams_webhook_url, json=payload, timeout=15)
    return r.ok