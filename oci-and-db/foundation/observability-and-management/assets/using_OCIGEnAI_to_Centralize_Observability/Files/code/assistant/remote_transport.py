"""Public HTTPS MCP transport; DNS is checked and pinned at the socket boundary."""
import asyncio
import ipaddress
import socket
from urllib.parse import urlsplit
import httpcore
import httpx
from httpcore._backends.auto import AutoBackend

def public_address(value):
    ip=ipaddress.ip_address(value)
    return ip.is_global and not (ip.is_reserved or ip.is_multicast or ip.is_unspecified or ip.is_loopback or ip.is_link_local)


def validate_remote_url(url):
    try:
        parsed=urlsplit(url)
        if parsed.scheme!='https' or not parsed.hostname or parsed.port not in {None,443} or parsed.username or parsed.password or parsed.query or parsed.fragment:
            raise ValueError()
        if len(url)>2048 or any(ord(c)<33 for c in url):raise ValueError()
        try:
            if not public_address(parsed.hostname):raise ValueError('Remote MCP must use a public HTTPS address')
        except ValueError as exc:
            if 'Remote MCP' in str(exc):raise
        if parsed.hostname.lower() in {'localhost','metadata.google.internal'} or parsed.hostname.lower().endswith(('.localhost','.local','.internal')):
            raise ValueError()
    except (ValueError,TypeError):
        raise ValueError('Use a public HTTPS MCP URL on port 443, without user info, query parameters or fragments.') from None
    return url


class PublicBackend(httpcore.AsyncNetworkBackend):
    def __init__(self):self.backend=AutoBackend()
    async def connect_tcp(self,host,port,timeout=None,local_address=None,socket_options=None):
        host=host.decode() if isinstance(host,bytes) else host
        records=await asyncio.wait_for(asyncio.get_running_loop().getaddrinfo(host,port,type=socket.SOCK_STREAM),timeout or 10)
        addresses=list(dict.fromkeys(r[4][0] for r in records))
        if not addresses or any(not public_address(ip) for ip in addresses):
            raise httpcore.ConnectError('Remote MCP resolved to a non-public address')
        # Use the checked literal address. HTTP Host and TLS SNI retain the original hostname.
        return await self.backend.connect_tcp(addresses[0],port,timeout,local_address,socket_options)
    async def connect_unix_socket(self,*a,**kw):raise httpcore.ConnectError('Unix sockets are not supported')
    async def sleep(self,seconds):await asyncio.sleep(seconds)


class PublicTransport(httpx.AsyncHTTPTransport):
    def __init__(self):
        super().__init__(trust_env=False,retries=0)
        # Pinned httpx/httpcore versions: retain their TLS/SNI implementation and replace DNS/socket creation.
        self._pool._network_backend=PublicBackend()


def public_client(headers):
    return httpx.AsyncClient(headers=headers,transport=PublicTransport(),trust_env=False,
        follow_redirects=False,timeout=httpx.Timeout(15,read=120))
