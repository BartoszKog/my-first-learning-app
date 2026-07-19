# Learning App — Developer Docs

Welcome to the developer documentation for the **Word Learning Application** — a Flet (Flutter + Python) app for learning vocabulary and definitions with spaced repetition.

These docs explain how *this* project routes screens, shares chrome, and sizes layouts. For Flet controls, `Page` APIs, and platform deployment, use the official [Flet documentation](https://flet.dev/docs) alongside the guides below.

## New here?

1. [Getting started](getting-started.md) — clone, `uv sync`, run the app or docs.
2. [Architecture](architecture/index.md) — overview, then [routing and screens](architecture/routing-and-screens.md) for Shell/Deep and the route map ([startup order](architecture/startup.md)).
3. [Navigation guide](guides/navigation.md) and [Layout guide](guides/layout.md) — how screens move and resize day to day.
4. [Adding a screen](guides/adding-a-screen.md) — step-by-step checklist once Shell/Deep and layout are clear.
5. [Concepts](concepts/routing.md) — routing, chrome, body registry, and the learning algorithm when you need the mechanism, not the recipe.
6. [API reference](reference/index.md) — generated signatures while you code; use it with the guides, not instead of them.

**How the layers differ:** Architecture maps the system, Guides are recipes, Concepts explain mechanisms, API Reference lists contracts and signatures.

For Flet control APIs and framework behavior, keep [flet.dev/docs](https://flet.dev/docs) open in parallel.

To clone the repo and run the app or docs locally, see
[Getting started](getting-started.md).

## Documentation map

<div class="grid cards" markdown>

-   :material-sitemap:{ .lg .middle } **Architecture**

    ---

    How routing, screens, layout, chrome, CSV storage, and startup wiring fit together.

    [Read architecture →](architecture/index.md)

-   :material-plus-box:{ .lg .middle } **Adding a screen**

    ---

    Step-by-step checklist for shell and deep routes.

    [Add a screen →](guides/adding-a-screen.md)

-   :material-compass:{ .lg .middle } **Guides**

    ---

    Task-oriented walkthroughs: navigation, layout, state, and import/export.

    [Navigation guide →](guides/navigation.md)

-   :material-lightbulb-outline:{ .lg .middle } **Concepts**

    ---

    Routing registry, shell chrome, body wrappers, shared tile bodies,
    learning queue, and reusable UI components.

    [Routing concept →](concepts/routing.md)

-   :material-api:{ .lg .middle } **API reference**

    ---

    Generated signatures and contracts for routing, layout, chrome, state, and
    CSV data.

    [Browse API →](reference/index.md)

-   :material-book-open-page-variant:{ .lg .middle } **Flet docs**

    ---

    Official reference for controls, theming, routing primitives, and deployment.

    [Open flet.dev/docs →](https://flet.dev/docs){:target="_blank"}

</div>

## Guides {#guides}

| Guide | When to open it |
| --- | --- |
| [Navigation](guides/navigation.md) | Move between shell and deep routes from UI code. |
| [Layout](guides/layout.md) | Choose `LayoutKind`, wrappers, and responsive sizing. |
| [Adding a screen](guides/adding-a-screen.md) | Register a new route and wire its control. |
| [State and persistence](guides/state-and-persistence.md) | Screen vs session vs preferences; theme keys and `AppTheme`. |
| [Import and export](guides/import-export.md) | Validate CSVs, import sets, and export through the shared picker. |

## Concepts {#concepts}

| Concept | When to open it |
| --- | --- |
| [Routing](concepts/routing.md) | How `RouteDef`, factories, and the router cooperate. |
| [Chrome and wrappers](concepts/chrome-and-wrappers.md) | Shared shell chrome (config + live `AppChrome` / drawer) and body wrappers. |
| [Body registry](concepts/body-registry.md) | Why home and export reuse one `TilesContainer` instance. |
| [Learning algorithm](concepts/learning-algorithm.md) | How `AppData` draws practice groups and saves answers. |
| [UI components](concepts/ui-components.md) | Tiles, learn fields, edit cards, and search controls. |

## Project layout

```text
main.py                   # thin launcher: ft.run(learning_app.app.main)
learning_app/
  app.py                  # app.main; wires chrome, theme, router handlers
  utils/
    greetings.py          # AppBar greeting text
  data/
    file_path_manager.py  # storage roots and csv_files paths
    app_data.py           # catalog CRUD, load/save, AppData session
    constants.py          # CSV column enums, MAX_ROWS, import messages
    csv_processor.py      # import validation and specialized saves
  ui/
    route_paths.py        # canonical path constants
    route_url.py          # build and parse route URLs
    route_registry.py     # RouteDef registry, drawer, build factories
    router.py             # view stack, layout dispatch, route events
    navigation.py         # navigate_to, push_view, go_back (screen authors)
    chrome_config.py      # ShellChromeConfig per shell route
    app_chrome.py         # Live AppBar / bottom bar / FAB / drawer registry
    app_drawer.py         # Shared NavigationDrawer for Shell destinations
    layout_host.py        # body wrappers: shell, deep, safe area
    layout_metrics.py     # responsive widths and breakpoint helpers
    layout_tokens.py      # shared spacing / sizing tokens
    page_functions.py     # shared dialogs and page helpers
    body_registry.py      # shared home/export TilesContainer instances
    routable_screen.py    # apply_layout protocol and view traversal
    app_session.py        # page, export FilePicker, navigation lock
    preferences.py        # SharedPreferences accessor
    screens/              # application screens (+ _screen_template.py)
    components/           # reusable controls
docs/                     # this documentation (MkDocs Material)
```

Clone and run steps are on [Getting started](getting-started.md). Source:
[github.com/BartoszKog/my-first-learning-app](https://github.com/BartoszKog/my-first-learning-app).
