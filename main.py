from typing import Any, List, Dict, Optional
import os
import urllib3
from mcp.server.fastmcp import FastMCP
import requests

# Suppress InsecureRequestWarning for self-signed UniFi certs
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Configuration
UNIFI_API_KEY = os.getenv("UNIFI_API_KEY", "CHANGEME")
UNIFI_GATEWAY_HOST = os.getenv("UNIFI_GATEWAY_HOST", "192.168.1.1")
UNIFI_GATEWAY_PORT = os.getenv("UNIFI_GATEWAY_PORT", "443")
UNIFI_GATEWAY_BASE_URL = f"https://{UNIFI_GATEWAY_HOST}:{UNIFI_GATEWAY_PORT}/proxy/network/integration"

MCP_HOST = os.getenv("MCP_HOST", "0.0.0.0")
MCP_PORT = int(os.getenv("MCP_PORT", "8000"))

# Initialize FastMCP server
mcp = FastMCP("unifi", host=MCP_HOST, port=MCP_PORT)


def unifi_request(
    path: str,
    method: str,
    params: Optional[Dict[str, Any]] = None,
    data: Optional[Dict[str, Any]] = None,
):
    """Make a request to the UniFi API."""
    url = f"{UNIFI_GATEWAY_BASE_URL}/{path}"
    headers = {
        "Content-Type": "application/json",
        "X-API-Key": UNIFI_API_KEY,
    }
    response = requests.request(
        method, url, headers=headers, params=params, json=data, verify=False
    )
    response.raise_for_status()
    return response.json()


# ---------------------------------------------------------------------------
# Resources
# ---------------------------------------------------------------------------

@mcp.resource("sites://")
async def list_sites() -> List[Dict[str, Any]]:
    """List all sites in the UniFi controller."""
    sites = []
    params = {"limit": 200, "offset": 0}
    while True:
        resp = unifi_request("/v1/sites", "GET", params=params)
        sites.extend(resp["data"])
        if resp["count"] != resp["limit"] or resp["totalCount"] <= len(sites):
            break
        params["offset"] += resp["limit"]
    return sites


@mcp.resource("sites://{site_id}/devices")
async def list_devices(site_id: str) -> List[Dict[str, Any]]:
    """List all adopted devices in a UniFi site."""
    devices = []
    params = {"limit": 200, "offset": 0}
    while True:
        resp = unifi_request(f"/v1/sites/{site_id}/devices", "GET", params=params)
        devices.extend(resp["data"])
        if resp["count"] != resp["limit"] or resp["totalCount"] <= len(devices):
            break
        params["offset"] += resp["limit"]
    return devices


@mcp.resource("sites://{site_id}/clients")
async def list_clients(site_id: str) -> List[Dict[str, Any]]:
    """List all connected clients in a UniFi site."""
    clients = []
    params = {"limit": 200, "offset": 0}
    while True:
        resp = unifi_request(f"/v1/sites/{site_id}/clients", "GET", params=params)
        clients.extend(resp["data"])
        if resp["count"] != resp["limit"] or resp["totalCount"] <= len(clients):
            break
        params["offset"] += resp["limit"]
    return clients


# ---------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------

@mcp.tool()
async def get_sites() -> List[Dict[str, Any]]:
    """Get all UniFi sites managed by this controller."""
    return await list_sites()


@mcp.tool()
async def get_devices(site_id: str) -> List[Dict[str, Any]]:
    """
    Get all adopted devices (APs, switches, gateways) for a given site.

    Args:
        site_id: The ID of the UniFi site.
    """
    return await list_devices(site_id)


@mcp.tool()
async def get_clients(site_id: str) -> List[Dict[str, Any]]:
    """
    Get all currently connected clients for a given site.

    Args:
        site_id: The ID of the UniFi site.
    """
    return await list_clients(site_id)


@mcp.tool()
async def get_device_stats(site_id: str, device_id: str) -> Dict[str, Any]:
    """
    Get detailed stats for a specific device.

    Args:
        site_id: The ID of the UniFi site.
        device_id: The ID of the device.
    """
    resp = unifi_request(f"/v1/sites/{site_id}/devices/{device_id}", "GET")
    return resp.get("data", resp)


if __name__ == "__main__":
    mcp.run(transport="sse")
