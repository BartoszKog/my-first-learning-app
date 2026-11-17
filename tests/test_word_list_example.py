"""Filled example sentences on definition cards in the word list."""

from types import SimpleNamespace

import flet as ft
import pandas as pd
import pytest

from learning_app.data.constants import EXAMPLE_SENTENCE_COLUMN, StatsColumns, WordDefinitions
from learning_app.data.set_settings import EffectiveSetSettings
from learning_app.ui.screens.word_list_menu import WordContainer


def _settings(*, example_speaker: bool) -> EffectiveSetSettings:
    return EffectiveSetSettings(
        kind="definitions",
        language="pl",
        auto_speak=True,
        speakers_word_formations=True,
        speakers_word=True,
        speakers_definition=False,
        speakers_example=example_speaker,
        retry_until_correct=True,
        queue_size=10,
        example_mode="after_check",
        uses_app_defaults=True,
    )


def _row(example: str | None) -> pd.Series:
    data: dict[str, object] = {
        WordDefinitions.DEFINITION.value: "control someone",
        WordDefinitions.WORD.value: "keep SB in line",
        StatsColumns.CORRECT_ANSWERS.value: 0,
        StatsColumns.GOOD_ANSWER.value: False,
        StatsColumns.GOOD_ANSWERS_IN_A_ROW.value: False,
        StatsColumns.WORD_TO_LEARN.value: False,
    }
    if example is not None:
        data[EXAMPLE_SENTENCE_COLUMN] = example
    return pd.Series(data)


def _field_rows(card: WordContainer) -> list[ft.Row]:
    column = card.content
    assert isinstance(column, ft.Column)
    return column.controls


def _shown(control: ft.Text) -> str:
    if control.spans:
        return "".join(span.text for span in control.spans)
    return control.value or ""


def test_definition_card_shows_the_filled_example():
    card = WordContainer(
        _row("I {keep/keeps} him {in line}."),
        400,
        settings=_settings(example_speaker=True),
    )
    rows = _field_rows(card)
    assert [row.controls[0].value for row in rows] == [
        "Definition ",
        "Word        ",
        "Example    ",
    ]
    example = rows[2].controls[1]
    assert _shown(example) == "I keep him in line."
    assert [span.text for span in example.spans if span.style is not None] == [
        "keep",
        "in line",
    ]
    assert any(isinstance(control, ft.IconButton) for control in rows[2].controls)


def test_example_row_stays_when_its_speaker_is_off():
    card = WordContainer(
        _row("I {keep} him {in line}."),
        250,
        settings=_settings(example_speaker=False),
    )
    example = _field_rows(card)[2]
    assert _shown(example.controls[1]) == "I keep him in line."
    assert [span.text for span in example.controls[1].spans if span.style is not None] == [
        "keep",
        "in line",
    ]
    assert all(not isinstance(control, ft.IconButton) for control in example.controls)


def test_card_without_an_example_omits_the_row():
    card = WordContainer(_row(None), 250, settings=_settings(example_speaker=True))
    labels = [row.controls[0].value for row in _field_rows(card)]
    assert labels == ["Definition ", "Word        "]


@pytest.mark.asyncio
async def test_example_speaker_reads_the_filled_sentence(monkeypatch):
    spoken = []

    async def fake_speak(text, language):
        spoken.append((text, language))

    monkeypatch.setattr(
        "learning_app.ui.screens.word_list_menu.AppSession.speak",
        fake_speak,
    )
    card = WordContainer(
        _row("I {keep/keeps} him {in line}."),
        250,
        settings=_settings(example_speaker=True),
    )
    button = next(
        control
        for control in _field_rows(card)[2].controls
        if isinstance(control, ft.IconButton)
    )
    await button.on_click(SimpleNamespace())
    assert spoken == [("I keep him in line.", "pl")]
