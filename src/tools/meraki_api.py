from typing import List, Dict, Any, Optional
import meraki
from ..settings import settings

# Jednorazová inicializácia Meraki SDK (má vlastný rate-limit backoff)
dashboard = meraki.DashboardAPI(
    api_key=settings.meraki_api_key,
    base_url="https://api.meraki.com/api/v1",
    output_log=False,
    print_console=False,
    suppress_logging=True
)

def list_networks(org_id: Optional[str] = None) -> List[Dict[str, Any]]:
    """Vráti zoznam networks v organizácii."""
    org = org_id or settings.meraki_org_id
    return dashboard.organizations.getOrganizationNetworks(org)

def list_devices(org_id: Optional[str] = None) -> List[Dict[str, Any]]:
    """Vráti zariadenia (sériové čísla v kľúči 'serial') priradené do sietí."""
    org = org_id or settings.meraki_org_id
    # stránkovanie cez SDK
    return dashboard.organizations.getOrganizationDevices(org, total_pages="all")

def get_wan_usage(org_id: Optional[str] = None, timespan_sec: int = 3600) -> List[Dict[str, Any]]:
    """WAN utilization (bytes sent/received) za timespan pre všetky MX/Z v org."""
    org = org_id or settings.meraki_org_id
    return dashboard.appliance.getOrganizationApplianceUplinksUsageByNetwork(
        org, timespan=timespan_sec
    )

def get_switch_port_usage(serial: str, timespan_sec: int = 3600) -> List[Dict[str, Any]]:
    """
    LAN (MS) port utilization pre daný switch (serial).
    Vracia polia vrátane usageInKb a trafficInKbps.
    """
    return dashboard.switch.getDeviceSwitchPortsStatuses(
        serial, timespan=timespan_sec
    )