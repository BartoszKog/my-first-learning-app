# Set settings

Source: `data/set_settings.py`

Per-set learning and TTS overrides stored as cells on `files.csv`. An empty
cell inherits the matching app setting from `TtsPreferences` or
`LearnPreferences`. Column rules are in
[Per-set settings](../architecture/data-and-storage.md#per-set-settings).
The screen is `/set/settings`.

::: learning_app.data.set_settings
