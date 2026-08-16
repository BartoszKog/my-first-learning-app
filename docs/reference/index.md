# API Reference

The API reference documents generated signatures and contracts for the UI
routing layer and the CSV data layer. Read
[Architecture](../architecture/index.md) and the
[Guides](../guides/adding-a-screen.md) first; use this tab while implementing
to confirm types, parameters, and return values.

## Routing & navigation

| Module | Source | Purpose | Use when | Related docs |
| --- | --- | --- | --- | --- |
| [Route paths](route_paths.md) | `ui/route_paths.py` | Canonical `"/…"` constants for every route. | Declaring or comparing paths without string typos. | [Adding a screen](../guides/adding-a-screen.md) |
| [Route URLs](route_url.md) | `ui/route_url.py` | Parse, build, and compare route URLs with query params. | Encoding `file_name` or `mode` in navigation calls. | [Navigation guide](../guides/navigation.md) |
| [Route registry](route_registry.md) | `ui/route_registry.py` | `RouteDef` entries, enums, drawer builder, `get_route`. | Registering a route or inspecting registry metadata. | [Routing concept](../concepts/routing.md) |
| [Navigation](navigation.md) | `ui/navigation.py` | `navigate_to`, `push_view`, `go_back`, `go_search`. | Moving between routes from screen and control code. | [Navigation guide](../guides/navigation.md) |
| [In-place search](inplace_search.md) | `ui/inplace_search.py` | Open/close search UI over shared tile bodies. | Debugging search chrome or calling search outside `go_search`. | [Body registry](../concepts/body-registry.md), [Navigation guide](../guides/navigation.md#open-search) |
| [Router](router.md) | `ui/router.py` | Route-change handlers, view construction, layout dispatch. | Wiring `app.py` or debugging stack replacement and push. | [Routing concept](../concepts/routing.md), [Startup](../architecture/startup.md) |

## Layout & chrome

| Module | Source | Purpose | Use when | Related docs |
| --- | --- | --- | --- | --- |
| [Routable screens](routable_screen.md) | `ui/routable_screen.py` | `apply_layout` protocol and active-view lookup. | Implementing responsive shell or deep controls. | [Layout guide](../guides/layout.md) |
| [Chrome configuration](chrome_config.md) | `ui/chrome_config.py` | `ShellChromeConfig` and per-route chrome map. | Tuning app bar, FAB, or bottom bar for a shell route. | [Chrome and wrappers](../concepts/chrome-and-wrappers.md) |
| [App chrome](app_chrome.md) | `ui/app_chrome.py` | Registry of live AppBar / bottom bar / FAB / drawer refs. | Applying Shell chrome or attaching shared controls to views. | [Chrome and wrappers](../concepts/chrome-and-wrappers.md), [Startup](../architecture/startup.md) |
| [App drawer](app_drawer.md) | `ui/app_drawer.py` | Shared `NavigationDrawer` for Shell destinations. | Changing drawer navigation or lock behavior. | [Chrome and wrappers](../concepts/chrome-and-wrappers.md) |
| [Layout host](layout_host.md) | `ui/layout_host.py` | Body-wrapper builders and width sync helpers. | Choosing or extending `BodyWrapperKind` hosts. | [Chrome and wrappers](../concepts/chrome-and-wrappers.md) |
| [Layout metrics](layout_metrics.md) | `ui/layout_metrics.py` | `LayoutMetrics`, store, and field-width helpers. | Reading breakpoints and computed widths in `apply_layout`. | [Layout guide](../guides/layout.md) |

## Shared state

| Module | Source | Purpose | Use when | Related docs |
| --- | --- | --- | --- | --- |
| [Body registry](body_registry.md) | `ui/body_registry.py` | Shared home and export `TilesContainer` accessors. | Search, export, or navigation that reuses tile bodies. | [Body registry concept](../concepts/body-registry.md) |
| [App session](app_session.md) | `ui/app_session.py` | Shared `Page`, export `FilePicker`, and navigation lock. | Wiring chrome/export at startup or locking navigation briefly. | [State and persistence](../guides/state-and-persistence.md) |
| [Preferences](preferences.md) | `ui/preferences.py` | `SharedPreferences` factory for durable settings. | Reading or writing user settings outside a screen instance. | [State and persistence](../guides/state-and-persistence.md) |
| [App theme](app_theme.md) | `ui/app_theme.py` | Theme mode and preference-backed page bgcolor. | Applying or persisting content background / mode. | [State and persistence](../guides/state-and-persistence.md#theming), [Startup](../architecture/startup.md) |

## Data & learning

| Module | Source | Purpose | Use when | Related docs |
| --- | --- | --- | --- | --- |
| [File path manager](file_path_manager.md) | `data/file_path_manager.py` | Storage roots and `csv_files/` path helpers. | Resolving where catalogs and set CSVs live. | [Data and storage](../architecture/data-and-storage.md) |
| [App data](app_data.md) | `data/app_data.py` | Catalog CRUD, load/save, empty sets, `AppData`. | Creating, listing, or learning a set on disk. | [Data and storage](../architecture/data-and-storage.md), [Learning algorithm](../concepts/learning-algorithm.md) |
| [Constants](constants.md) | `data/constants.py` | Column enums, `MAX_ROWS`, import messages. | Matching CSV schemas or import error text. | [Data and storage](../architecture/data-and-storage.md), [Import and export](../guides/import-export.md) |
| [CSV processor](csv_processor.md) | `data/csv_processor.py` | Validate, repair catalog, import save helpers. | Importing a set or checking `files.csv`. | [Import and export](../guides/import-export.md) |
| [Demo sets](demo_sets.md) | `data/demo_sets.py` | Bundled demos, reserved names, install into storage. | Adding sample sets or protecting demo basenames. | [Data and storage](../architecture/data-and-storage.md#demo-sets) |

## Suggested order for new contributors

1. [Route paths](route_paths.md) and [Route URLs](route_url.md) — vocabulary for paths and parameters.
2. [Route registry](route_registry.md) — where routes are declared.
3. [Navigation](navigation.md) — what screen code calls day to day.
4. [In-place search](inplace_search.md) — when tracing search UI without a route.
5. [Routable screens](routable_screen.md), [Layout metrics](layout_metrics.md), and [Layout host](layout_host.md) — responsive behavior.
6. [Chrome configuration](chrome_config.md) and [App chrome](app_chrome.md) — declarative Shell chrome vs live control registry ([App drawer](app_drawer.md) when changing drawer navigation).
7. [File path manager](file_path_manager.md), [Constants](constants.md), and [App data](app_data.md) — where sets live on disk; read [Learning algorithm](../concepts/learning-algorithm.md) with `AppData`.
8. [CSV processor](csv_processor.md) and [Demo sets](demo_sets.md) — import/catalog repair and bundled sample install.
9. [Preferences](preferences.md) and [App theme](app_theme.md) — durable settings and content background.
10. [Router](router.md) — only when you change startup wiring or trace a route event.

Private `_build_*` factories and internal layout dispatchers are hidden from
these pages. They remain in source for router maintainers.
