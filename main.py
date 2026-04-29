from typing import Any, List, Dict, Optional
import os
import sys
import urllib3
from mcp.server.fastmcp import FastMCP
import requests

# Suppress InsecureRequestWarning for self-signed UniFi certs
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Build metadata
BUILD_TIMESTAMP = os.getenv("BUILD_TIMESTAMP", "unknown")
BUILD_VERSION = os.getenv("BUILD_VERSION", "unknown")[:7]  # short SHA

# Configuration
UNIFI_API_KEY = os.getenv("UNIFI_API_KEY", "CHANGEME")
SITE_MANAGER_BASE_URL = "https://api.ui.com"

# Local UDM access for devices/clients (optional)
UNIFI_GATEWAY_HOST = os.getenv("UNIFI_GATEWAY_HOST", "")
UNIFI_GATEWAY_PORT = os.getenv("UNIFI_GATEWAY_PORT", "443")

MCP_HOST = os.getenv("MCP_HOST", "0.0.0.0")
MCP_PORT = int(os.getenv("MCP_PORT", "8000"))


def print_banner():
    banner = f"""
╔══════════════════════════════════════════════╗
║                                              ║
║   ██╗   ██╗███╗   ██╗██╗███████╗██╗         ║
║   ██║   ██║████╗  ██║██║██╔════╝██║         ║
║   ██║   ██║██╔██╗ ██║██║█████╗  ██║         ║
║   ██║   ██║██║╚██╗██║██║██╔══╝  ██║         ║
║   ╚██████╔╝██║ ╚████║██║██║     ██║         ║
║    ╚═════╝ ╚═╝  ╚═══╝╚═╝╚═╝     ╚═╝         ║
║                                              ║
║        MCP Server for UniFi Networks         ║
║                                              ║
║  Build : {BUILD_VERSION:<36} ║
║  Built : {BUILD_TIMESTAMP:<36} ║
║                                              ║
╚══════════════════════════════════════════════╝
"""
    print(banner, file=sys.stderr)


print_banner()

# Initialize FastMCP server
mcp = FastMCP("unifi", host=MCP_HOST, port=MCP_PORT)


def site_manager_request(
    path: str,
    method: str = "GET",
    params: Optional[Dict[str, Any]] = None,
    data: Optional[Dict[str, Any]] = None,
) -> Any:
    """Make a request to the UniFi Site Manager cloud API."""
    url = f"{SITE_MANAGER_BASE_URL}/{path.lstrip('/')}"
    headers = {
        "X-API-KEY": UNIFI_API_KEY,
        "Accept": "application/json",
        "Content-Type": "application/json",
    }
    response = requests.request(
        method, url, headers=headers, params=params, json=data, verify=True
    )
    response.raise_for_status()
    return response.json()


def local_request(
    path: str,
    method: str = "GET",
    params: Optional[Dict[str, Any]] = None,
    data: Optional[Dict[str, Any]] = None,
) -> Any:
    """Make a request to the local UDM Network Application API."""
    if not UNIFI_GATEWAY_HOST:
        raise ValueError(
            "UNIFI_GATEWAY_HOST is not set. Local UDM access is required for devices/clients."
        )
    base_url = f"https://{UNIFI_GATEWAY_HOST}:{UNIFI_GATEWAY_PORT}/proxy/network/integration"
    url = f"{base_url}/{path.lstrip('/')}"
    headers = {
        "X-API-KEY": UNIFI_API_KEY,
        "Accept": "application/json",
        "Content-Type": "application/json",
    }
    response = requests.request(
        method, url, headers=headers, params=params, json=data, verify=False
    )
    response.raise_for_status()
    return response.json()


def paginate_site_manager(path: str, params: Optional[Dict] = None) -> List[Dict]:
    """Paginate through Site Manager API results."""
    results = []
    p = {"limit": 200, "offset": 0, **(params or {})}
    while True:
        resp = site_manager_request(path, params=p)
        data = resp.get("data", [])
        results.extend(data)
        total = resp.get("totalCount", len(data))
        if len(results) >= total or len(data) < p["limit"]:
            break
        p["offset"] += p["limit"]
    return results


def paginate_local(path: str, params: Optional[Dict] = None) -> List[Dict]:
    """Paginate through local UDM API results."""
    results = []
    p = {"limit": 200, "offset": 0, **(params or {})}
    while True:
        resp = local_request(path, params=p)
        data = resp.get("data", [])
        results.extend(data)
        total = resp.get("totalCount", len(data))
        if len(results) >= total or len(data) < p["limit"]:
            break
        p["offset"] += p["limit"]
    return results


# ---------------------------------------------------------------------------
# Tools -- Site Manager API (cloud)
# ---------------------------------------------------------------------------

@mcp.tool()
async def get_hosts() -> List[Dict[str, Any]]:
    """Get all UniFi consoles (hosts) registered to this account."""
    return paginate_site_manager("/v1/hosts")


@mcp.tool()
async def get_sites() -> List[Dict[str, Any]]:
    """Get all UniFi sites across all consoles."""
    return paginate_site_manager("/v1/sites")


@mcp.tool()
async def get_site_devices(host_id: str) -> List[Dict[str, Any]]:
    """
    Get devices for a specific host via the Site Manager API.

    Args:
        host_id: The host ID from get_hosts().
    """
    return paginate_site_manager("/v1/devices", params={"hostId": host_id})


# ---------------------------------------------------------------------------
# Tools -- Local UDM API (requires UNIFI_GATEWAY_HOST to be set)
# ---------------------------------------------------------------------------

@mcp.tool()
async def get_local_sites() -> List[Dict[str, Any]]:
    """
    Get all sites from the local UDM Network Application.
    Requires UNIFI_GATEWAY_HOST environment variable to be set.
    """
    return paginate_local("/v1/sites")


@mcp.tool()
async def get_local_devices(site_id: str) -> List[Dict[str, Any]]:
    """
    Get all adopted devices for a site from the local UDM.
    Requires UNIFI_GATEWAY_HOST environment variable to be set.

    Args:
        site_id: The site ID from get_local_sites().
    """
    return paginate_local(f"/v1/sites/{site_id}/devices")


@mcp.tool()
async def get_local_clients(site_id: str) -> List[Dict[str, Any]]:
    """
    Get all connected clients for a site from the local UDM.
    Requires UNIFI_GATEWAY_HOST environment variable to be set.

    Args:
        site_id: The site ID from get_local_sites().
    """
    return paginate_local(f"/v1/sites/{site_id}/clients")


@mcp.tool()
async def get_local_device_stats(site_id: str, device_id: str) -> Dict[str, Any]:
    """
    Get detailed stats for a specific device from the local UDM.
    Requires UNIFI_GATEWAY_HOST environment variable to be set.

    Args:
        site_id: The site ID from get_local_sites().
        device_id: The device ID from get_local_devices().
    """
    resp = local_request(f"/v1/sites/{site_id}/devices/{device_id}")
    return resp.get("data", resp)


if __name__ == "__main__":
    mcp.run(transport="sse")