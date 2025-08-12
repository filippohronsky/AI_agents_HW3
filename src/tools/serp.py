from typing import List, Dict, Any
from serpapi import GoogleSearch
from ..settings import settings

def search_security_threats(query: str, num: int = 5) -> List[Dict[str, Any]]:
    """
    Jednoduché vyhľadanie hrozieb cez SerpAPI (Google).
    Príklad query: 'Meraki CVE site:cisa.gov OR site:nvd.nist.gov past month'
    """
    params = {
        "engine": "google",
        "q": query,
        "num": num,
        "api_key": settings.serpapi_api_key,
    }
    res = GoogleSearch(params).get_dict()
    return res.get("organic_results", [])[:num]