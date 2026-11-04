# TTS

Source: `tts/`

Pronunciation backend: provider contract, gTTS implementation, content-addressed
MP3 cache, live-set phrase collection, and `TtsService`. Cache layout and GC
rules are in [Data and storage](../architecture/data-and-storage.md#tts-cache).
Playback stays on [App session](app_session.md) (`speak`); the language and
auto-speak used for a set are its effective overrides, with
[TTS preferences](tts_preferences.md) as the app default. Screens must not
construct `Audio` or `GttsProvider`.

## Provider

::: learning_app.tts.provider

::: learning_app.tts.gtts_provider

## Cache and texts

::: learning_app.tts.cache

::: learning_app.tts.texts

## Service

::: learning_app.tts.service
