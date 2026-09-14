# Learn preferences

Source: `ui/learn_preferences.py`

Process-wide learn-session flags, loaded from and saved to preferences.
Ownership and the retry key are in
[State and persistence](../guides/state-and-persistence.md#learning);
startup restore order is in [Startup](../architecture/startup.md). Queue
rules stay on `AppData` — see
[Learning algorithm](../concepts/learning-algorithm.md#retry-until-correct).

::: learning_app.ui.learn_preferences
