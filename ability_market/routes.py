"""URL normalization shared with the marketplace; no checkout side effects."""
import re
URL_RE = re.compile(r"^https?://[^\s]+\.[^\s]+$")

def normalize_target_url(raw):
    """Turn what a customer actually types into a URL we can scan.

    Matching URL_RE against raw input rejected almost everything real: people
    type "visionaid.org", they paste "www.visionaid.org", and phone keyboards
    capitalise the first letter, so "Https://visionaid.org" arrived and was
    refused. That cost us live orders - a buyer hit the same error over and
    over with no way through.

    So: add https:// when no scheme was given, and lower-case the scheme and
    host. Anything after the host is left exactly as typed, because paths and
    query strings are case-sensitive. Returns "" if there is still nothing
    usable, and never coerces a non-http scheme into one (file://, javascript:
    and friends stay rejected). The SSRF guard in the scanner still runs on
    whatever comes out of here.
    """
    value = (raw or "").strip().strip("<>").rstrip(".,")
    if not value:
        return ""
    scheme_match = re.match(r"^(https?)://(.*)$", value, re.IGNORECASE)
    if scheme_match:
        value = scheme_match.group(1).lower() + "://" + scheme_match.group(2)
    elif "://" in value or re.match(r"^[a-zA-Z][a-zA-Z0-9+.\-]*:", value):
        return ""  # some other scheme - reject rather than rewrite it
    else:
        value = "https://" + value
    head, sep, tail = value.partition("://")
    host, slash, rest = tail.partition("/")
    value = head + sep + host.lower() + slash + rest
    return value if URL_RE.match(value) else ""
