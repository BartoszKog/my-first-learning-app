# Demo sets

Source: `data/demo_sets.py`

Bundled sample CSV templates under `src/assets/demos/`, reserved basename
protection for create/import, and `install_demo_sets()` used by Settings.
Install reads a template and registers the set in the database. Conceptual
flow is in
[Data and storage](../architecture/data-and-storage.md#demo-sets).

::: learning_app.data.demo_sets
