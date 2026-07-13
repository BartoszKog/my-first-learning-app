# API Reference

The API reference documents generated signatures and contracts for the UI
routing layer. Read [Architecture](../architecture.md) and the
[Guides](../guides/adding-a-screen.md) first; use this tab while implementing
to confirm types, parameters, and return values.

## Module map

| Module | Purpose | Use when | Related docs |
| --- | --- | --- | --- |
| [Route paths](route_paths.md) | Canonical `"/…"` constants for every route. | Declaring or comparing paths without string typos. | [Adding a screen](../guides/adding-a-screen.md) |
| [Route URLs](route_url.md) | Parse, build, and compare route URLs with query params. | Encoding `file_name` or `mode` in navigation calls. | [Navigation guide](../guides/navigation.md) |
| [Route registry](route_registry.md) | `RouteDef` entries, enums, drawer builder, `get_route`. | Registering a route or inspecting registry metadata. | [Routing concept](../concepts/routing.md) |
| [Navigation](navigation.md) | `navigate_to`, `push_view`, `go_back`, `go_search`. | Moving between routes from screen and control code. | [Navigation guide](../guides/navigation.md) |
| [Routable screens](routable_screen.md) | `apply_layout` protocol and active-view lookup. | Implementing responsive shell or deep controls. | [Layout guide](../guides/layout.md) |
| [Chrome configuration](chrome_config.md) | `ShellChromeConfig` and per-route chrome map. | Tuning app bar, FAB, or bottom bar for a shell route. | [Chrome and wrappers](../concepts/chrome-and-wrappers.md) |
| [Layout host](layout_host.md) | Body-wrapper builders and width sync helpers. | Choosing or extending `BodyWrapperKind` hosts. | [Chrome and wrappers](../concepts/chrome-and-wrappers.md) |
| [Layout metrics](layout_metrics.md) | `LayoutMetrics`, store, and field-width helpers. | Reading breakpoints and computed widths in `apply_layout`. | [Layout guide](../guides/layout.md) |
| [Body registry](body_registry.md) | Shared home and export `TilesContainer` accessors. | Search, export, or navigation that reuses tile bodies. | [Body registry concept](../concepts/body-registry.md) |
| [App session](app_session.md) | In-memory session bag for multi-step workflows. | Holding transient state across views in one run. | [State and persistence](../guides/state-and-persistence.md) |
| [Preferences](preferences.md) | `SharedPreferences` factory for durable settings. | Reading or writing user settings outside a screen instance. | [State and persistence](../guides/state-and-persistence.md) |
| [Router](router.md) | Route-change handlers, view construction, layout dispatch. | Wiring `app.py` or debugging stack replacement and push. | [Routing concept](../concepts/routing.md) |

## Suggested order for new contributors

1. [Route paths](route_paths.md) and [Route URLs](route_url.md) — vocabulary for paths and parameters.
2. [Route registry](route_registry.md) — where routes are declared.
3. [Navigation](navigation.md) — what screen code calls day to day.
4. [Routable screens](routable_screen.md), [Layout metrics](layout_metrics.md), and [Layout host](layout_host.md) — responsive behavior.
5. [Router](router.md) — only when you change startup wiring or trace a route event.

Private `_build_*` factories and internal layout dispatchers are hidden from
these pages. They remain in source for router maintainers.
