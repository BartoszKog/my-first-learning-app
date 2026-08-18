# App Session

Source: `ui/app_session.py`

Process-wide runtime services: the live `Page`, the shared export `FilePicker`,
the session `TtsService`, a lazily created `flet_audio.Audio` player (mounted
on first `speak`, never with an empty `src`), and a temporary navigation lock
for drawer / bottom bar / FAB. A newer `speak` takes over the remaining
slash-separated playlist; the current clip is not paused or stopped. Not a
general store for form fields or domain data — see
[State and persistence](../guides/state-and-persistence.md)
([Text to speech](../guides/state-and-persistence.md#text-to-speech)).

::: learning_app.ui.app_session
