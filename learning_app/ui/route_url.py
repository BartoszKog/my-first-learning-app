from urllib.parse import parse_qs, quote, unquote, urlencode, urlparse


def route_path(route: str | None) -> str:
    return urlparse(route or "/").path


def route_params(route: str | None) -> dict[str, str]:
    parsed = urlparse(route or "")
    if not parsed.query:
        return {}
    return {
        key: unquote(values[0])
        for key, values in parse_qs(parsed.query, keep_blank_values=True).items()
        if values
    }


def build_route(path: str, **params) -> str:
    query_params = {key: str(value) for key, value in params.items() if value is not None}
    if not query_params:
        return path
    return f"{path}?{urlencode(query_params, quote_via=quote)}"


def routes_match(left: str | None, right: str | None) -> bool:
    return (left or "") == (right or "")
