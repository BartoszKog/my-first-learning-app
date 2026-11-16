# File Path Manager

Source: `data/file_path_manager.py`

Resolves Flet storage directories, `learning.sqlite` beside `csv_files/`,
and `tts_cache/`. Call `initialize()` and then `init_db()` at startup before
loading or saving sets.
See [Data and storage](../architecture/data-and-storage.md).

::: learning_app.data.file_path_manager
