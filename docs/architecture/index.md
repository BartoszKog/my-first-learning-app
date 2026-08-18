# Architecture

The application renders each URL as a Flet `ft.View`. Public navigation
helpers change the route, the router resolves a registered route definition,
and the selected screen factory supplies the view body. Route metadata keeps
screen construction, chrome, wrappers, and resize behavior separate.

**Start here for navigation:**
[Routing and screens](routing-and-screens.md) — routing flow, Shell versus
Deep, and the route → class map.

Learning-set content and progress live outside the routing layer as CSV files
under application storage. See [Data and storage](data-and-storage.md).

How `app.py` wires storage, session, chrome, theme, TTS preferences, and the
first Home route is described in [Startup and lifecycle](startup.md).

## Module responsibilities

### Entrypoint

| Module | Responsibility |
| --- | --- |
| `app.py` | Creates the page and application-level services. See [Startup and lifecycle](startup.md). |

### Data & learning

| Module | Responsibility |
| --- | --- |
| `data/file_path_manager.py` | Resolves storage directories, CSV paths, and the TTS cache root. |
| `data/app_data.py` | Set catalog CRUD, load/save, and in-memory learning session state. |
| `data/constants.py` | CSV column enums, row cap, and import error/warning messages. |
| `data/csv_processor.py` | Import validation, repair, and save paths for CSV sets. |
| `data/demo_sets.py` | Bundled demo templates, reserved basenames, and install into storage. |
| `tts/` | Cached pronunciations, gTTS provider, and garbage collection. |

See [Data and storage](data-and-storage.md) for how these modules fit together.

### Routing & navigation

| Module | Responsibility |
| --- | --- |
| `ui/navigation.py` | Exposes the supported navigation operations. |
| `ui/route_paths.py` | Defines reusable route path constants. |
| `ui/route_url.py` | Parses, builds, and compares route URLs with query parameters. |
| `ui/route_registry.py` | Declares routes and their factories, layout, chrome, drawer, and fallback metadata. |
| `ui/router.py` | Builds and restores the view stack and dispatches layout updates. |

See [Routing and screens](routing-and-screens.md) for flow, Shell/Deep roles,
and the screen map.

### Layout & chrome

| Module | Responsibility |
| --- | --- |
| `ui/layout_host.py` | Wraps route bodies with the required sizing and safe-area behavior. |
| `ui/chrome_config.py` | Configures shared Shell chrome per route. |
| `ui/app_chrome.py` | Registry of live AppBar / bottom bar / FAB / drawer controls. |
| `ui/app_drawer.py` | Shared navigation drawer for Shell destinations. |
| `ui/layout_metrics.py` | Computes reusable responsive dimensions. |
| `ui/layout_tokens.py` | Shared layout ratios and sizing constants used by metrics. |
| `ui/routable_screen.py` | `apply_layout` protocol and active-view lookup for responsive screens. |

### Shared UI state

| Module | Responsibility |
| --- | --- |
| `ui/body_registry.py` | Shared Home and export `TilesContainer` accessors for in-place search. |
| `ui/app_session.py` | In-memory session bag for app-wide runtime UI services (including TTS playback). |
| `ui/preferences.py` | `SharedPreferences` factory for durable settings. |
| `ui/app_theme.py` | Theme mode and preference-backed page bgcolor. |
| `ui/tts_preferences.py` | TTS language and auto-speak flags backed by preferences. |

### Screens

| Module | Responsibility |
| --- | --- |
| `ui/screens/` | Contains route-specific controls and behavior. |
| `ui/components/` | Reusable bodies used by routes (for example Home `TilesContainer`). |

## Continue reading

- [Routing and screens](routing-and-screens.md)
- [Data and storage](data-and-storage.md)
- [Startup and lifecycle](startup.md)
- [Learning algorithm](../concepts/learning-algorithm.md)
- [UI components](../concepts/ui-components.md)
- [Import and export](../guides/import-export.md)
- [Add a screen](../guides/adding-a-screen.md)
- [Navigate and pass route data](../guides/navigation.md)
- [Implement responsive layout](../guides/layout.md)
- [Choose state and persistence](../guides/state-and-persistence.md)
- [Understand the body registry](../concepts/body-registry.md)
