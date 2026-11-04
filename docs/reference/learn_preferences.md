# Learn preferences

Source: `ui/learn_preferences.py`

Process-wide learn-session defaults, loaded from and saved to preferences.
A set with empty override cells uses these values; a stored cell replaces
them. Ownership and the retry key are in
[State and persistence](../guides/state-and-persistence.md#learning);
per-set cells are in
[Per-set settings](../architecture/data-and-storage.md#per-set-settings).
Startup restore order is in [Startup](../architecture/startup.md). Queue
rules stay on `AppData` — see
[Learning algorithm](../concepts/learning-algorithm.md#retry-until-correct).

::: learning_app.ui.learn_preferences
