# TTS preferences

Source: `ui/tts_preferences.py`

Process-wide TTS language, auto-speak, and word-list speaker defaults,
loaded from and saved to preferences. A set with empty override cells uses
these values. Ownership and preference keys are in
[State and persistence](../guides/state-and-persistence.md#text-to-speech);
per-set cells are in
[Per-set settings](../architecture/data-and-storage.md#per-set-settings).
Startup restore order is in [Startup](../architecture/startup.md).

::: learning_app.ui.tts_preferences
