# Learning App — Developer Docs

Welcome to the developer documentation for the **Word Learning Application** — a Flet (Flutter + Python) app for learning vocabulary and definitions with spaced repetition.

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

    *Coming soon: `adding-a-screen.md`*

-   :material-file-code:{ .lg .middle } **Screen template**

    ---

    Reference implementation in `learning_app/ui/screens/_screen_template.py`.

-   :material-github:{ .lg .middle } **Source code**

    ---

    [github.com/BartoszKog/my-first-learning-app](https://github.com/BartoszKog/my-first-learning-app)

</div>

## Project layout

```text
learning_app/
  app.py              # Flet entrypoint
  data/               # CSV processing, constants
  ui/
    route_paths.py    # route path constants
    route_registry.py # RouteDef registry, drawer, build factories
    router.py         # view stack, layout dispatch
    navigation.py     # navigate_to, push_view, go_back
    screens/          # application screens
    components/       # reusable controls
docs/                 # this documentation (MkDocs Material)
```
