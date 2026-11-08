# CSV Processor

Source: `data/csv_processor.py`

Import validation and save helpers that write a picked CSV into the database.
`validate_files_csv` and `repair_files_csv` still target a leftover catalog
file; Home and import do not call them.

Task flow and UI wiring are in the
[Import and export guide](../guides/import-export.md). Message enums live in
the [Constants API](constants.md).

::: learning_app.data.csv_processor
