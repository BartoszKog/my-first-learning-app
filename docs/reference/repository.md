# Repository

Source: `data/repository.py`

One SQLite engine per process, short sessions, and the public load, save,
catalog, visit, override, and export operations. Screens should keep calling
`data/app_data.py` and `data/set_settings.py`. Startup calls `init_db()` after
`FilePathManager.initialize()`. Behavior is in
[Data and storage](../architecture/data-and-storage.md).

::: learning_app.data.repository
