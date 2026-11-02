"""Lightweight security helpers: CSRF tokens, per-IP rate limiting, SSRF guard.

No external dependencies. Designed for a single small Flask app; rate-limit
state is per-process (good enough on Cloud Run; each instance limits abuse).
"""

import ipaddress
import secrets
import socket
import threading
import time
from collections import defaultdict, deque
from urllib.parse import urlparse

from flask import request, session

# ---------------------------------------------------------------------------
# CSRF
# ---------------------------------------------------------------------------

def get_csrf_token():
    """Return the session CSRF token, creating one if needed."""
    token = session.get("csrf_token")
    if not token:
        token = secrets.token_urlsafe(32)
        session["csrf_token"] = token
    return token


def csrf_valid():
    """True if the submitted CSRF token matches the session token."""
    sent = (request.form.get("csrf_token", "")
            or request.headers.get("X-CSRF-Token", ""))
    expected = session.get("csrf_token", "")
    return bool(expected) and secrets.compare_digest(sent, expected)


# ---------------------------------------------------------------------------
# Rate limiting (per client IP, per bucket, sliding window)
# ---------------------------------------------------------------------------

_hits = defaultdict(deque)
_rl_lock = threading.Lock()


def client_ip():
    fwd = request.headers.get("X-Forwarded-For", "")
    if fwd:
        return fwd.split(",")[0].strip()
    return request.remote_addr or "unknown"


def rate_limited(bucket, limit, window_s):
    """Record a hit; return True if the caller has exceeded `limit` per window."""
    key = (bucket, client_ip())
    now = time.time()
    with _rl_lock:
        dq = _hits[key]
        cutoff = now - window_s
        while dq and dq[0] < cutoff:
            dq.popleft()
        if len(dq) >= limit:
            return True
        dq.append(now)
        # opportunistic cleanup to bound memory
        if len(_hits) > 5000:
            for k in list(_hits.keys()):
                if not _hits[k] or _hits[k][-1] < cutoff:
                    _hits.pop(k, None)
        return False


# ---------------------------------------------------------------------------
# SSRF guard for the scanner (block internal / metadata targets)
# ---------------------------------------------------------------------------

def url_is_public(url, timeout=5):
    """Return (ok, reason). Rejects non-http(s), and hosts that resolve to
    private, loopback, link-local, reserved, or multicast addresses — which
    prevents the scanner from being used to reach internal services or the
    cloud metadata endpoint (169.254.169.254)."""
    try:
        p = urlparse(url)
    except Exception:
        return False, "unparseable URL"
    if p.scheme not in ("http", "https"):
        return False, "only http/https allowed"
    host = p.hostname
    if not host:
        return False, "no host"
    # Block obvious metadata / localhost names
    lowered = host.lower()
    if lowered in ("localhost", "metadata", "metadata.google.internal"):
        return False, "blocked host"
    try:
        infos = socket.getaddrinfo(host, p.port or (443 if p.scheme == "https" else 80),
                                   proto=socket.IPPROTO_TCP)
    except Exception:
        return False, "DNS resolution failed"
    for info in infos:
        addr = info[4][0]
        try:
            ip = ipaddress.ip_address(addr)
        except ValueError:
            return False, "invalid resolved address"
        if (ip.is_private or ip.is_loopback or ip.is_link_local
                or ip.is_reserved or ip.is_multicast or ip.is_unspecified):
            return False, f"resolves to non-public address ({addr})"
    return True, "ok"
