import ipaddress
import aiohttp
import json

from .constants import IP_API_URL

async def fetch_public_ip() -> str:
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(IP_API_URL, timeout=5) as resp:

                resp.raise_for_status()
                data = await resp.json()
                return data["ip"]
    except Exception as e:
        raise RuntimeError(f"Network error fetching public IP: {e}")

def normalize_ip(value: str) -> str:
    if "/" in value: return value
    try:
        ip = ipaddress.ip_address(value)
        return f"{value}/32" if ip.version == 4 else f"{value}/128"
    except ValueError: 
        raise ValueError(f"Invalid IP address: {value}")
