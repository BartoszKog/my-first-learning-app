# Body registry

Source: `ui/body_registry.py`

Home and Import/Export each own a `TilesContainer`. Search should filter the
same container the user was already viewing: constructing a second copy would
duplicate controls and could show state different from the source screen.

`BodyRegistry` solves this narrow coordination problem by retaining references
to the active Home and export tile bodies.

## Home flow

The Home factory creates and registers its body:

```python
body = TilesContainer(page)
BodyRegistry.set_home(body)
return [body]
```

Screen code calls `go_search(page, mode="home")`. Internally, the helper
selects that same instance before pushing Search:

```python
body = BodyRegistry.get_home()
if body.has_content_tiles():
    push_view(page, SEARCH_ROUTE, mode="home")
```

The complete flow is:

```text
TilesContainer → BodyRegistry.set_home() → go_search(mode="home") → SearchScreen
```

Search is a Deep route: it reuses the same tile body, without shared Shell
chrome.

![Search filtering the Home tile body](../assets/architecture/search-screen.png){ .docs-screenshot-sm }

## Import/Export flow

`ImportExportControl` creates the export body lazily and reuses it on later
visits:

```python
if not BodyRegistry.has_export():
    tiles_of_sets = TilesContainer(page, export_mode=True)
    BodyRegistry.set_export(tiles_of_sets)
else:
    tiles_of_sets = BodyRegistry.get_export()
```

Likewise, `go_search(page, mode="export")` internally selects the export body:

```python
body = BodyRegistry.get_export()
if body.has_content_tiles():
    push_view(page, SEARCH_ROUTE, mode="export")
```

The flow is:

```text
TilesContainer → BodyRegistry.set_export() → go_search(mode="export") → SearchScreen
```

Before pushing Search, `go_search()` verifies that the selected body contains
tiles. The Search route factory also checks that the requested registry entry
exists; if no body is available, it returns `None` and the route fallback is
used.

## Scope of the registry

This is process-wide UI coordination, not general application state. Store
only the Home and export `TilesContainer` references here.

Do not use `BodyRegistry` for:

- learning-set or other domain data,
- persisted settings,
- route parameters,
- form fields,
- unrelated controls shared only for convenience.

See [State and persistence](../guides/state-and-persistence.md) for choosing
the correct owner and lifetime for other values.

See the [Body registry API](../reference/body_registry.md) for its generated
method contracts.
