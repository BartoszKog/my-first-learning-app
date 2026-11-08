# Getting started

Clone the repository, install dependencies with [uv](https://docs.astral.sh/uv/),
and run the Flet app or these docs locally.

## Prerequisites

- [Git](https://git-scm.com/)
- [uv](https://docs.astral.sh/uv/getting-started/installation/) (manages Python
  and dependencies)
- Python **3.12+** (uv can install it if needed)

## Clone

```bash
git clone https://github.com/BartoszKog/my-first-learning-app.git
cd my-first-learning-app
```

Repository:
[github.com/BartoszKog/my-first-learning-app](https://github.com/BartoszKog/my-first-learning-app).

## Run the application

From the repository root:

```bash
uv sync
uv run flet run .
```

`uv sync` creates the virtual environment and installs runtime dependencies.
The thin launcher `src/main.py` calls `ft.run` on
`learning_app.app.main`. Application code and Flet assets live under `src/`
so packaging (`flet build` / `flet test`) does not include `docs/` or `tests/`.

## Serve these docs

Install the `dev` dependency group (MkDocs Material, mkdocstrings, …), then
serve:

```bash
uv sync --group dev
uv run mkdocs serve
```

Open [http://127.0.0.1:8000](http://127.0.0.1:8000) in your browser.

Build a static site into `site/`:

```bash
uv run mkdocs build
```

## Troubleshooting

| Symptom | What to check |
| --- | --- |
| Sets missing after restart | Confirm `FilePathManager.initialize()` and `init_db()` ran, and that `learning.sqlite` under `FLET_APP_STORAGE_DATA` (or the CWD fallback) is writable. See [Data and storage](architecture/data-and-storage.md). |
| Old CSV sets did not appear | Startup copies only rows listed in `files.csv` whose set file can be read, and only once. A CSV dropped into `csv_files/` without a catalog row is not a set. |
| Docs build noisy / `--strict` fails | Prefer `uv run mkdocs build` without `--strict` while iterating. Strict mode can fail on Griffe type-annotation warnings from generated API pages (for example `app_theme`). |

## Next steps

1. [Architecture](architecture/index.md) — how the package is wired.
2. [Navigation](guides/navigation.md) and [Layout](guides/layout.md) — day-to-day routing and sizing.
3. [Adding a screen](guides/adding-a-screen.md) — first change workflow.
4. [Home](index.md) — full documentation map.
