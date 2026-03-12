"""
Безопасное извлечение реального IP клиента из trusted proxy заголовков.
"""

import ipaddress
from dataclasses import dataclass

from fastapi import Request

# Official Cloudflare reverse proxy IP ranges:
# https://www.cloudflare.com/ips-v4
# https://www.cloudflare.com/ips-v6
CLOUDFLARE_IP_RANGES = (
    "173.245.48.0/20",
    "103.21.244.0/22",
    "103.22.200.0/22",
    "103.31.4.0/22",
    "141.101.64.0/18",
    "108.162.192.0/18",
    "190.93.240.0/20",
    "188.114.96.0/20",
    "197.234.240.0/22",
    "198.41.128.0/17",
    "162.158.0.0/15",
    "104.16.0.0/13",
    "104.24.0.0/14",
    "172.64.0.0/13",
    "131.0.72.0/22",
    "2400:cb00::/32",
    "2606:4700::/32",
    "2803:f800::/32",
    "2405:b500::/32",
    "2405:8100::/32",
    "2a06:98c0::/29",
    "2c0f:f248::/32",
)

_CLOUDFLARE_NETWORKS = tuple(ipaddress.ip_network(cidr) for cidr in CLOUDFLARE_IP_RANGES)


@dataclass(frozen=True, slots=True)
class ClientIPInfo:
    value: str | None
    source: str


def extract_client_ip(request: Request) -> ClientIPInfo:
    """
    Возвращает реальный IP клиента.

    CF-Connecting-IP доверяем только если ближайший upstream IP относится к Cloudflare
    или если запрос пришел через локальный cloudflared tunnel.
    Это не дает внешнему клиенту подделать заголовок на DNS-only поддомене,
    но позволяет принимать Telegram webhook через Cloudflare Tunnel.
    """
    client_host = request.client.host if request.client else None
    x_real_ip = request.headers.get("X-Real-IP")
    x_forwarded_for = request.headers.get("X-Forwarded-For")
    cf_connecting_ip = request.headers.get("CF-Connecting-IP")

    proxy_ip = (
        _first_valid_ip(x_real_ip)
        or _first_valid_ip(_first_forwarded_ip(x_forwarded_for))
        or _first_valid_ip(client_host)
    )

    if cf_connecting_ip and proxy_ip and _is_trusted_cf_proxy(proxy_ip):
        trusted_cf_ip = _first_valid_ip(cf_connecting_ip)
        if trusted_cf_ip:
            return ClientIPInfo(value=trusted_cf_ip, source="CF-Connecting-IP")

    for source, candidate in (
        ("X-Real-IP", x_real_ip),
        ("X-Forwarded-For", _first_forwarded_ip(x_forwarded_for)),
        ("client.host", client_host),
    ):
        valid_ip = _first_valid_ip(candidate)
        if valid_ip:
            return ClientIPInfo(value=valid_ip, source=source)

    return ClientIPInfo(value=None, source="unresolved")


def _first_forwarded_ip(forwarded_for: str | None) -> str | None:
    if not forwarded_for:
        return None
    return forwarded_for.split(",", 1)[0].strip()


def _first_valid_ip(value: str | None) -> str | None:
    if not value:
        return None

    candidate = value.strip()
    try:
        ipaddress.ip_address(candidate)
    except ValueError:
        return None
    return candidate


def _is_cloudflare_ip(value: str) -> bool:
    try:
        ip = ipaddress.ip_address(value)
    except ValueError:
        return False
    return any(ip in network for network in _CLOUDFLARE_NETWORKS)


def _is_loopback_ip(value: str) -> bool:
    try:
        return ipaddress.ip_address(value).is_loopback
    except ValueError:
        return False


def _is_trusted_cf_proxy(value: str) -> bool:
    return _is_cloudflare_ip(value) or _is_loopback_ip(value)
