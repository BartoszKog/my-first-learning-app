"""Parse, build, and compare application route URLs."""

from urllib.parse import parse_qs, quote, unquote, urlencode, urlparse


def route_path(route: str | None) -> str:
    """Extract the path component of a route URL.

    Args:
        route: Route URL, or ``None`` to use the root route.

    Returns:
        The URL path component.
    """
    return urlparse(route or "/").path


def route_params(route: str | None) -> dict[str, str]:
    """Decode the first value of each route query parameter.

    Args:
        route: Route URL to parse. ``None`` is treated as an empty URL.

    Returns:
        A mapping of query parameter names to decoded string values.
    """
    parsed = urlparse(route or "")
    if not parsed.query:
        return {}
    return {
        key: unquote(values[0])
        for key, values in parse_qs(parsed.query, keep_blank_values=True).items()
        if values
    }


def build_route(path: str, **params: object) -> str:
    """Build a route URL from a path and optional query parameters.

    Args:
        path: Route path to preserve as the URL base.
        **params: Query parameter values. ``None`` values are omitted and all
            other values are converted to strings.

    Returns:
        The path, followed by an encoded query string when parameters remain.
    """
    query_params = {key: str(value) for key, value in params.items() if value is not None}
    if not query_params:
        return path
    return f"{path}?{urlencode(query_params, quote_via=quote)}"


def routes_match(left: str | None, right: str | None) -> bool:
    """Compare two complete route strings without normalization.

    Args:
        left: First route, with ``None`` treated as an empty string.
        right: Second route, with ``None`` treated as an empty string.

    Returns:
        ``True`` when both complete route strings are equal.
    """
    return (left or "") == (right or "")
