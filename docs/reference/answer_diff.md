# Answer diff

Source: `data/answer_diff.py`

Letter-level diff between a typed answer and the stored answer. After a wrong,
non-blank Check, `WordField.feedback` shows the typed text with `wrong` runs
struck through and `missing` runs inserted. Below `CLOSE_MATCH_RATIO` the
typed text is shown without marks. See
[UI components](../concepts/ui-components.md).

::: learning_app.data.answer_diff
