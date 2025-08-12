from typing import Any, Dict, List
from langchain.tools import tool
from langgraph.prebuilt import create_react_agent

from ..settings import settings
from ..tools import meraki_api, storage, serp, teams

# --- Tools (deklarované pre LLM) ---

@tool("list_networks", return_direct=False)
def list_networks_tool(_: str = "") -> str:
    """Vráť dostupné Meraki networks v organizácii."""
    nets = meraki_api.list_networks()
    storage.save_networks(nets)
    return f"Načítaných {len(nets)} sietí. Dáta uložené do tabuľky 'networks'."

@tool("list_devices", return_direct=False)
def list_devices_tool(_: str = "") -> str:
    """Vráť zariadenia v Meraki organizácii (vr. sériových čísel)."""
    devs = meraki_api.list_devices()
    storage.save_devices(devs)
    serials = [d.get("serial") for d in devs if d.get("serial")]
    return f"Zariadení: {len(devs)}. Príklad 5 sérií: {serials[:5]}"

@tool("wan_utilization", return_direct=False)
def wan_utilization_tool(timespan_hours: int = 6) -> str:
    """
    Získaj WAN utilization (bytes sent/received per uplink) za posledné hodiny pre všetky siete.
    """
    rows = meraki_api.get_wan_usage(timespan_sec=timespan_hours * 3600)
    storage.save_wan_usage(rows)
    # krátka sumarizácia
    nets = {r["networkId"]: r.get("name", "") for r in rows}
    return f"WAN záznamov: {len(rows)}, sietí: {len(nets)}. Uložené do 'wan_usage'."

@tool("lan_utilization", return_direct=False)
def lan_utilization_tool(input_str: str) -> str:
    """
    Získaj LAN (switch port) utilization pre daný switch SERIAL a timespan v minútach.
    Formát: SERIAL;MINUTES  (napr. Q2XX-XXXX-ABCD;60)
    """
    try:
        serial, minutes = input_str.split(";")
        minutes = int(minutes)
    except Exception:
        return "Použi formát SERIAL;MINUTES, napr. Q2XX-XXXX-ABCD;60"

    rows = meraki_api.get_switch_port_usage(serial.strip(), timespan_sec=minutes * 60)
    cnt = storage.save_switch_ports(serial.strip(), rows)
    # vypíš top porty podľa trafficInKbps.total (ak prítomné)
    top = sorted(
        rows,
        key=lambda r: (r.get("trafficInKbps") or {}).get("total", 0.0),
        reverse=True
    )[:5]
    tops = [f"{r.get('portId')}={ (r.get('trafficInKbps') or {}).get('total', 0.0) } kbps" for r in top]
    return f"Uložených portov: {cnt}. Top5: {', '.join(tops)}"

@tool("security_threats_search", return_direct=False)
def security_threats_search_tool(query: str) -> str:
    """Vyhľadaj bezpečnostné hrozby (SerpAPI). Vráti top odkazy."""
    items = serp.search_security_threats(query, num=5)
    lines = [f"- {i.get('title')}: {i.get('link')}" for i in items]
    return "Nálezy:\n" + "\n".join(lines)

@tool("teams_notify", return_direct=False)
def teams_notify_tool(text: str) -> str:
    """Pošli notifikáciu do MS Teams (Incoming Webhook)."""
    ok = teams.post_to_teams(text=text, title="MerakiOps Agent")
    return "Odoslané do Teams." if ok else "TEAMS_WEBHOOK_URL nenastavené alebo požiadavka zlyhala."

TOOLS = [list_networks_tool, list_devices_tool, wan_utilization_tool,
         lan_utilization_tool, security_threats_search_tool, teams_notify_tool]

# --- LLM model (OpenAI alebo Ollama) ---
def _llm():
    if settings.llm_provider.lower() == "openai":
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(model=settings.llm_model, temperature=0)
    else:
        from langchain_ollama import ChatOllama
        return ChatOllama(model=settings.llm_model, base_url=settings.ollama_host, temperature=0)

# --- ReAct agent v LangGraph ---
def build_agent():
    model = _llm()
    SYS = (
        "Si MerakiOps ReAct agent. VŽDY použi tooly, nie halucinácie.\n"
        "- WAN => zavolaj tool `wan_utilization(timespan_hours=...)`.\n"
        "- LAN => zavolaj `lan_utilization` s formátom 'SERIAL;MINUTES' a vysvetli, "
        "  ak zariadenie nie je MS switch.\n"
        "Odpovedaj stručne po slovensky."
    )
    return create_react_agent(model, TOOLS, prompt=SYS)