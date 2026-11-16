# App Data

Source: `data/app_data.py`

Public catalog helpers, load/save against the local database (content cells
kept as text, with `checks` and `card_id` on the frame), empty-set
construction, Home-tile progress (`get_set_learn_progress`), and the
in-memory `AppData` learning session. Storage layout is in
[Data and storage](../architecture/data-and-storage.md). Queue rules and
answer transitions are in
[Learning algorithm](../concepts/learning-algorithm.md).

::: learning_app.data.app_data
