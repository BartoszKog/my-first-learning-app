# Learning App — Developer Docs

Welcome to the developer documentation for the **Word Learning Application** — a Flet (Flutter + Python) app for learning vocabulary and definitions with spaced repetition.

These docs explain how *this* project routes screens, shares chrome, and sizes layouts. For Flet controls, `Page` APIs, and platform deployment, use the official [Flet documentation](https://flet.dev/docs) alongside the guides below.

## New here?

Follow this path when you add or change screens:

1. [Architecture](architecture.md) — how routing, views, chrome, and layout fit together.
2. [Adding a screen](guides/adding-a-screen.md) — step-by-step checklist for shell and deep routes.
3. [Navigation guide](guides/navigation.md) and [Layout guide](guides/layout.md) — day-to-day tasks after the first screen works.
4. [Concepts](concepts/routing.md) — routing, chrome, and body registry when you need the mechanism, not the recipe.
5. [API reference](reference/index.md) — generated signatures while you code; use it with the guides, not instead of them.

For Flet control APIs and framework behavior, keep [flet.dev/docs](https://flet.dev/docs) open in parallel.

## Quick start

Run the application:

```bash
uv sync
uv run flet run .
```

Serve these docs locally:

```bash
uv sync --group dev
uv run mkdocs serve
```

Open [http://127.0.0.1:8000](http://127.0.0.1:8000) in your browser.

Build static site output to `site/`:

```bash
uv run mkdocs build
```

## Documentation map

<div class="grid cards" markdown>

-   :material-sitemap:{ .lg .middle } **Architecture**

    ---

    How routing, views, layout, chrome, and screen lifecycle fit together.

    [Read architecture →](architecture.md)

-   :material-plus-box:{ .lg .middle } **Adding a screen**

    ---

    Step-by-step checklist for shell and deep routes.

    [Add a screen →](guides/adding-a-screen.md)

-   :material-compass:{ .lg .middle } **Guides**

    ---

    Task-oriented walkthroughs: navigation, layout, and state ownership.

    [Navigation guide →](guides/navigation.md)

-   :material-lightbulb-outline:{ .lg .middle } **Concepts**

    ---

    Routing registry, shell chrome, body wrappers, and shared tile bodies.

    [Routing concept →](concepts/routing.md)

-   :material-api:{ .lg .middle } **API reference**

    ---

    Generated signatures and contracts for routing, layout, chrome, and state.

    [Browse API →](reference/index.md)

-   :material-book-open-page-variant:{ .lg .middle } **Flet docs**

    ---

    Official reference for controls, theming, routing primitives, and deployment.

    [Open flet.dev/docs →](https://flet.dev/docs){:target="_blank"}

</div>

## Guides {#guides}

| Guide | When to open it |
| --- | --- |
| [Adding a screen](guides/adding-a-screen.md) | Register a new route and wire its control. |
| [Navigation](guides/navigation.md) | Move between shell and deep routes from UI code. |
| [Layout](guides/layout.md) | Choose `LayoutKind`, wrappers, and responsive sizing. |
| [State and persistence](guides/state-and-persistence.md) | Decide what lives on the screen, in session, or in preferences. |

## Concepts {#concepts}

| Concept | When to open it |
| --- | --- |
| [Routing](concepts/routing.md) | How `RouteDef`, factories, and the router cooperate. |
| [Chrome and wrappers](concepts/chrome-and-wrappers.md) | Shared shell chrome and body-wrapper choices. |
| [Body registry](concepts/body-registry.md) | Why home and export reuse one `TilesContainer` instance. |

## Project layout

```text
learning_app/
  app.py              # Flet entrypoint; wires router handlers
  data/               # CSV processing, constants
  ui/
    route_paths.py    # canonical path constants
    route_url.py      # build and parse route URLs
    route_registry.py # RouteDef registry, drawer, build factories
    router.py         # view stack, layout dispatch, route events
    navigation.py     # navigate_to, push_view, go_back (screen authors)
    chrome_config.py  # ShellChromeConfig per shell route
    layout_host.py    # body wrappers: shell, deep, safe area
    layout_metrics.py # responsive widths and breakpoint helpers
    body_registry.py  # shared home/export TilesContainer instances
    routable_screen.py# apply_layout protocol and view traversal
    app_session.py    # in-memory session state for active workflows
    preferences.py    # SharedPreferences accessor
    screens/          # application screens
    components/       # reusable controls
docs/                 # this documentation (MkDocs Material)
```

The source repository is available at
[github.com/BartoszKog/my-first-learning-app](https://github.com/BartoszKog/my-first-learning-app).
