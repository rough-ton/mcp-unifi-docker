# mcp-server-unifi (Unraid / Docker SSE Edition)

A containerized MCP server exposing your UniFi network to AI agents (Claude Desktop, Goose, etc.) via SSE transport. Designed to run persistently on Unraid.

---

## Prerequisites

- UniFi API key: Settings > Control Plane > Integrations > Create API Key
- Docker installed (Unraid has this built in)
- Your UniFi gateway IP (default: `192.168.1.1`)

---

## Option 1: Build and Deploy on Unraid (Recommended)

### Step 1 — Copy files to Unraid

Copy this directory to your Unraid server, e.g.:

```
scp -r ./mcp-server-unifi root@YOUR_UNRAID_IP:/mnt/user/appdata/mcp-server-unifi
```

### Step 2 — Build the image on Unraid

SSH into Unraid and run:

```bash
cd /mnt/user/appdata/mcp-server-unifi
docker build -t mcp-server-unifi:latest .
```

### Step 3 — Add the container in the Unraid UI

Go to **Docker > Add Container** and fill in:

| Field | Value |
|---|---|
| Name | `mcp-server-unifi` |
| Repository | `mcp-server-unifi:latest` |
| Network Type | `Bridge` |
| Port | Host: `8000` / Container: `8000` / TCP |
| Restart Policy | `Unless Stopped` |

Add the following environment variables:

| Variable | Value |
|---|---|
| `UNIFI_API_KEY` | Your API key from UniFi |
| `UNIFI_GATEWAY_HOST` | Your gateway IP (e.g. `192.168.1.1`) |
| `UNIFI_GATEWAY_PORT` | `443` |

Click **Apply**.

---

## Option 2: Local Test with docker-compose

```bash
export UNIFI_API_KEY=your-key-here
export UNIFI_GATEWAY_HOST=192.168.1.1
docker compose up --build
```

---

## Connecting Claude Desktop

Edit `~/Library/Application Support/Claude/claude_desktop_config.json` (macOS) or `%APPDATA%\Claude\claude_desktop_config.json` (Windows):

```json
{
  "mcpServers": {
    "unifi": {
      "url": "http://YOUR_UNRAID_IP:8000/sse"
    }
  }
}
```

Restart Claude Desktop. You should see the UniFi MCP server listed under connected tools.

---

## Available Tools

| Tool | Description |
|---|---|
| `get_sites` | List all UniFi sites |
| `get_devices(site_id)` | List adopted APs, switches, gateways |
| `get_clients(site_id)` | List currently connected clients |
| `get_device_stats(site_id, device_id)` | Detailed stats for a specific device |

## Available Resources

| URI | Description |
|---|---|
| `sites://` | All sites |
| `sites://{site_id}/devices` | Devices for a site |
| `sites://{site_id}/clients` | Clients for a site |

---

## Updating

To update after code changes:

```bash
cd /mnt/user/appdata/mcp-server-unifi
docker build -t mcp-server-unifi:latest .
docker restart mcp-server-unifi
```

---

## Security Note

The UniFi gateway uses a self-signed TLS certificate. SSL verification is intentionally disabled for gateway requests only (`verify=False`). The MCP server itself does not use TLS — keep it on your LAN or behind a reverse proxy if you need external access.
