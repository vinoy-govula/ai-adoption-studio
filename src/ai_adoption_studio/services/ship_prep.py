"""Ship prep artifact helpers for Stage 3 production handover."""

from __future__ import annotations

from pathlib import Path
from typing import Any
from urllib.parse import urlparse


def write_nginx_reference(lead_dir: Path, manifest: dict[str, Any]) -> Path:
    """Write a customer nginx reference snippet tailored to manifest URLs."""
    access = manifest.get("access", {})
    public_url = access.get("public_url", "https://playground.example.com")
    parsed = urlparse(public_url)
    hostname = parsed.hostname or "playground.example.com"

    content = f"""# Generated ship-prep reference for {hostname}
# Source template: deployment-catalog/edge/customer-managed/nginx.reference.conf

upstream ai_gateway {{
    server gateway-host:8000;
}}

upstream ai_control_centre {{
    server control-centre-host:8002;
}}

server {{
    listen 443 ssl http2;
    server_name {hostname};

    location = /healthz {{
        proxy_pass http://ai_gateway/healthz;
    }}

    location /api/v1/ {{
        proxy_pass http://ai_gateway;
        proxy_buffering off;
        proxy_read_timeout 3600s;
    }}

    location /control-centre/ {{
        proxy_pass http://ai_control_centre/;
    }}
}}
"""
    out_dir = lead_dir / "ship-prep"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "nginx.reference.conf"
    out_path.write_text(content, encoding="utf-8")
    return out_path


CUSTOMER_EDGE_REFERENCES: list[tuple[str, str]] = [
    ("nginx", "deployment-catalog/edge/customer-managed/nginx.reference.conf"),
    ("Traefik", "deployment-catalog/edge/customer-managed/traefik.reference.yml"),
    ("Caddy", "deployment-catalog/edge/customer-managed/Caddyfile.reference"),
    ("Azure Application Gateway", "deployment-catalog/edge/customer-managed/azure-app-gateway.reference.md"),
    ("AWS ALB", "deployment-catalog/edge/customer-managed/aws-alb.reference.md"),
]
