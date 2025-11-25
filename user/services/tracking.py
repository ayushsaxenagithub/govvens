import json
import logging
import re
import uuid
from functools import lru_cache
from typing import Dict

import requests
from django.conf import settings

logger = logging.getLogger(__name__)

BOT_KEYWORDS = [
    "bot",
    "crawler",
    "spider",
    "slurp",
    "curl",
    "wget",
    "python-requests",
]
MOBILE_KEYWORDS = ["iphone", "android", "mobile", "opera mini", "blackberry"]
TABLET_KEYWORDS = ["ipad", "tablet", "kindle"]
DESKTOP_KEYWORDS = ["windows", "macintosh", "x11", "linux"]


def get_client_ip(request) -> str | None:
    """
    Resolve client IP while considering proxy headers.
    """
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded_for:
        ip = x_forwarded_for.split(",")[0].strip()
        if ip:
            return ip
    return request.META.get("REMOTE_ADDR")


def get_or_create_visitor_id(request):
    cookie_name = getattr(
        settings, "TRACKING_VISITOR_COOKIE_NAME", "gov_visitor_id"
    )
    current = request.COOKIES.get(cookie_name)
    if current:
        return current, False
    return uuid.uuid4().hex, True


def detect_device(user_agent: str) -> Dict[str, str]:
    agent = user_agent.lower()
    device_type = "unknown"

    if any(keyword in agent for keyword in BOT_KEYWORDS):
        device_type = "bot"
    elif any(keyword in agent for keyword in MOBILE_KEYWORDS):
        device_type = "mobile"
    elif any(keyword in agent for keyword in TABLET_KEYWORDS):
        device_type = "tablet"
    elif any(keyword in agent for keyword in DESKTOP_KEYWORDS):
        device_type = "desktop"

    browser_match = re.search(
        r"(chrome|safari|firefox|edge|opr|opera|msie|trident)/?\s*(\d+\.?\d*)",
        agent,
    )
    browser = ""
    version = ""
    if browser_match:
        browser = browser_match.group(1)
        version = browser_match.group(2)
        if browser == "opr":
            browser = "opera"
        if browser in {"msie", "trident"}:
            browser = "ie"

    os_match = re.search(
        r"(windows nt|mac os x|android|linux|iphone os|ipad; cpu os)\s*([\d_\.]+)?",
        agent,
    )
    operating_system = ""
    if os_match:
        operating_system = os_match.group(0).replace("_", ".")

    return {
        "device_type": device_type,
        "browser": browser.title(),
        "browser_version": version,
        "os": operating_system.title(),
        "is_bot": device_type == "bot",
    }


@lru_cache(maxsize=512)
def lookup_geo_data(ip_address: str | None) -> Dict[str, any]:
    """
    Query a public geolocation endpoint. Responses are cached in-process.
    Uses ip-api.com as primary (free, no API key required) with fallback to ipapi.co
    """
    if not ip_address:
        return {}
    
    # Skip local/private IPs
    if ip_address.startswith(("127.", "10.", "192.168", "172.16", "172.17", "172.18", 
                              "172.19", "172.20", "172.21", "172.22", "172.23", "172.24",
                              "172.25", "172.26", "172.27", "172.28", "172.29", "172.30",
                              "172.31", "169.254", "::1", "localhost")):
        return {}

    timeout = getattr(settings, "TRACKING_GEOIP_TIMEOUT", 3)
    
    # Primary: ip-api.com (free, no API key, 45 requests/minute)
    try:
        url = f"http://ip-api.com/json/{ip_address}?fields=status,message,country,regionName,city,lat,lon,isp,org,as,query"
        response = requests.get(url, timeout=timeout)
        if response.status_code == 200:
            data = response.json()
            if data.get("status") == "success":
                return {
                    "country": data.get("country", ""),
                    "region": data.get("regionName", ""),
                    "city": data.get("city", ""),
                    "latitude": float(data.get("lat", 0)) if data.get("lat") else None,
                    "longitude": float(data.get("lon", 0)) if data.get("lon") else None,
                    "isp": data.get("isp", "") or data.get("org", "") or data.get("as", ""),
                }
    except Exception as exc:
        logger.debug("ip-api.com lookup failed for %s: %s", ip_address, exc)
    
    # Fallback: ipapi.co
    try:
        url = f"https://ipapi.co/{ip_address}/json/"
        response = requests.get(url, timeout=timeout, headers={"User-Agent": "Django-Tracking/1.0"})
        if response.status_code == 200:
            payload = response.json()
            # Check for error in response
            if "error" not in payload:
                return {
                    "country": payload.get("country_name") or payload.get("country", ""),
                    "region": payload.get("region", "") or payload.get("region_code", ""),
                    "city": payload.get("city", ""),
                    "latitude": float(payload.get("latitude", 0)) if payload.get("latitude") else None,
                    "longitude": float(payload.get("longitude", 0)) if payload.get("longitude") else None,
                    "isp": payload.get("org", "") or payload.get("asn", ""),
                }
    except Exception as exc:
        logger.debug("ipapi.co lookup failed for %s: %s", ip_address, exc)
    
    # Final fallback: ip-api.com without fields (simpler response)
    try:
        url = f"http://ip-api.com/json/{ip_address}"
        response = requests.get(url, timeout=timeout)
        if response.status_code == 200:
            data = response.json()
            if data.get("status") == "success":
                return {
                    "country": data.get("country", ""),
                    "region": data.get("regionName", ""),
                    "city": data.get("city", ""),
                    "latitude": float(data.get("lat", 0)) if data.get("lat") else None,
                    "longitude": float(data.get("lon", 0)) if data.get("lon") else None,
                    "isp": data.get("isp", "") or data.get("org", ""),
                }
    except Exception as exc:
        logger.debug("Final geo lookup fallback failed for %s: %s", ip_address, exc)
    
    return {}


def extract_utm(request):
    params = request.GET
    return {
        "utm_source": params.get("utm_source", ""),
        "utm_medium": params.get("utm_medium", ""),
        "utm_campaign": params.get("utm_campaign", ""),
        "utm_term": params.get("utm_term", ""),
    }


def parse_json_body(request):
    if not request.body:
        return {}
    try:
        return json.loads(request.body.decode("utf-8"))
    except Exception:
        return {}

