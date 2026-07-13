# Navigation

Application code should use helpers from `learning_app/ui/navigation.py`
instead of manipulating `page.views` directly. Import route constants from
`route_paths.py`.

Choose the helper from the navigation intent:

- Main Shell destination → `navigate_to()` or `navigate_to_async()`.
- Focused Deep task → `push_view()`.
- Close the active Deep task → `go_back()`.
- Search the active tile source → `go_search()`.

See [Two navigation roles](../architecture.md#two-navigation-roles) if the
Shell/Deep distinction is not yet clear.

## Open a Shell screen

Use `navigate_to(page, route, **params)` from synchronous code:

```python
from learning_app.ui.navigation import navigate_to
from learning_app.ui.route_paths import HOME_ROUTE

navigate_to(page, HOME_ROUTE)
```

`navigate_to()` replaces the current view stack with the requested Shell
destination. Use it when changing the application's main screen, rather than
when opening a temporary task above the current screen.

Use `navigate_to_async()` inside async handlers. The drawer uses this form
because its open and close operations are asynchronous.

```python
await navigate_to_async(page, HOME_ROUTE)
```

## Open and close a Deep screen

`push_view()` keeps the current view available beneath the focused screen:

```python
from learning_app.ui.navigation import push_view
from learning_app.ui.route_paths import SET_EDIT_ROUTE

push_view(
    page,
    SET_EDIT_ROUTE,
    file="animals_words.csv",
    title="Animals",
)
```

`push_view()` is the normal entry point for a registered Deep route. If it
receives a Shell route, the router does not push that route onto the stack; it
falls back to the same stack-replacement behavior as `navigate_to()`. Call
`navigate_to()` directly for Shell navigation so the intent remains clear.

The parameters become a query string:

```text
/set/edit?file=animals_words.csv&title=Animals
```

`build_route()` converts every non-`None` value to text and URL-encodes it.
The router decodes the query into `dict[str, str]`, so factories receive route
parameters as strings even when the caller supplied another value type.

The build factory reads the parsed values:

```python
def _build_edit_set_controls(
    page: ft.Page,
    params: dict[str, str],
) -> list[ft.Control] | None:
    file_name = params.get("file")
    title = params.get("title")
```

If required data is absent, the factory can return `None`. The router then
builds the route configured in `RouteDef.fallback_path`; when no fallback is
configured, it uses Home. This prevents an incomplete Deep screen from being
shown with missing input.

```python
def _build_edit_set_controls(
    page: ft.Page,
    params: dict[str, str],
) -> list[ft.Control] | None:
    file_name = params.get("file")
    if not file_name:
        return None
    return [EditSetMenu(file_name)]


RouteDef(
    # ...
    build_factory=_build_edit_set_controls,
    fallback_path=HOME_ROUTE,
)
```

Close a Deep screen with `go_back()`:

```python
ft.Button(content="Cancel", on_click=lambda e: go_back(e.page))
```

## Open search

`go_search(page, mode="home")` opens search for the active tile source.
Supported modes are `"home"` and `"export"`:

```python
go_search(page, mode="export")
```

Search obtains that source through the
[body registry](../concepts/body-registry.md). If the selected
`TilesContainer` has no content tiles, `go_search()` returns without opening a
new view.

See the [Navigation API](../reference/navigation.md) and
[Route URL API](../reference/route_url.md) for complete signatures and
parameter encoding contracts. `RouteDef` and `fallback_path` are documented
in the [Route registry API](../reference/route_registry.md).
