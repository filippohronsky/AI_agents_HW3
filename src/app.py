import json
import typer
from rich.console import Console
from src.agent.graph import build_agent

app = typer.Typer(help="MerakiOps ReAct agent (LangGraph)")
console = Console()

@app.command()
def chat(prompt: str):
    """
    Pošli agentovi otázku v prirodzenom jazyku.
    Príklady:
      - "Vylistuj siete a zariadenia"
      - "Získaj WAN utilization za 6 hodín"
      - "LAN pre Q2XX-XXXX-ABCD za 60 min"
      - "Vyhľadaj nové hrozby pre Meraki tento týždeň"
    """
    agent = build_agent()
    # prebuilt agent vracia generátor krokov; použijeme simple invoke
    result = agent.invoke({"messages": [("user", prompt)]})
    # result["messages"] je konverzácia; poslednú správu vytiahneme
    last = result["messages"][-1]
    console.print(last.content)

@app.command()
def wan(hours: int = 6):
    """Skratka: WAN utilization z posledných N hodín (uloží do DB)."""
    agent = build_agent()
    out = agent.invoke({"messages": [("user", f"Získaj WAN utilization za {hours} hodín a ulož výsledok")]})
    console.print(out["messages"][-1].content)

@app.command()
def lan(serial: str, minutes: int = 60):
    """Skratka: LAN utilizácia pre switch SERIAL za N minút (uloží do DB)."""
    agent = build_agent()
    out = agent.invoke({"messages": [("user", f"Získaj LAN pre {serial} za {minutes} minút") ]})
    console.print(out["messages"][-1].content)

@app.command()
def bootstrap():
    """Inicializačný krok: uloží networks a devices (so sériami) do DB."""
    agent = build_agent()
    agent.invoke({"messages": [("user", "Vylistuj siete v Meraki a ulož ich do DB")]})
    agent.invoke({"messages": [("user", "Vylistuj zariadenia v Meraki (so sériami) a ulož ich do DB")]})
    console.print("[green]Hotovo.[/green]")

if __name__ == "__main__":
    app()