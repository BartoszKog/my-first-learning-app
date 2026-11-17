"""Example sentences on a definition card during a learn session."""

from types import SimpleNamespace

import pandas as pd
import pytest

from learning_app.data.app_data import generate_empty_files_data, save_set
from learning_app.data.constants import (
    EXAMPLE_SENTENCE_COLUMN,
    FilesColumns,
    StatsColumns,
    WordDefinitions,
)
from learning_app.data.set_settings import enable_set_overrides, set_override_value
from learning_app.ui.learn_preferences import LearnPreferences
from learning_app.ui.tts_preferences import TtsPreferences

FILE_NAME = "example_definitions.csv"


@pytest.fixture
def restore_flags():
    retry = LearnPreferences.retry_until_correct
    mode = LearnPreferences.example_mode
    auto_speak = TtsPreferences.auto_speak_definitions
    yield
    LearnPreferences.retry_until_correct = retry
    LearnPreferences.example_mode = mode
    TtsPreferences.auto_speak_definitions = auto_speak


@pytest.fixture
def silent_flet_updates(monkeypatch):
    monkeypatch.setattr("flet.Control.update", lambda self: None, raising=False)


def _save_set(example: str) -> None:
    generate_empty_files_data()
    save_set(
        pd.DataFrame(
            {
                WordDefinitions.DEFINITION.value: ["control someone"],
                WordDefinitions.WORD.value: ["keep SB in line"],
                EXAMPLE_SENTENCE_COLUMN: [example],
                StatsColumns.CORRECT_ANSWERS.value: [0],
                StatsColumns.GOOD_ANSWERS_IN_A_ROW.value: [False],
                StatsColumns.GOOD_ANSWER.value: [False],
                StatsColumns.WORD_TO_LEARN.value: [False],
            }
        ),
        FILE_NAME,
    )


def _start(mode: str, example: str = "I {keep/keeps} him {in line}."):
    from learning_app.ui.components.word_definition_field import WordDefinitionField

    _save_set(example)
    LearnPreferences.example_mode = mode
    LearnPreferences.retry_until_correct = True
    TtsPreferences.auto_speak_definitions = False
    screen = WordDefinitionField(FILE_NAME, session=True)
    screen.start()
    return screen


def _shown_text(screen) -> str:
    return "".join(span.text for span in screen.exampleText.spans)


def _check(screen, typed: str) -> None:
    screen.word.value = typed
    screen.on_check_click(SimpleNamespace())


def test_hint_shows_blank_gaps_then_fills_them(
    isolated_csv_dir, restore_flags, silent_flet_updates
):
    screen = _start("hint")
    assert screen.exampleText.visible is True
    assert _shown_text(screen) == "I _____ him _____."

    _check(screen, "keep SB in line")

    assert _shown_text(screen) == "I keep him in line."


def test_after_check_hides_example_until_check(
    isolated_csv_dir, restore_flags, silent_flet_updates
):
    screen = _start("after_check")
    assert screen.exampleText.visible is False

    _check(screen, "nope")

    assert screen.exampleText.visible is True
    assert _shown_text(screen) == "I keep him in line."


def test_off_never_shows_example(isolated_csv_dir, restore_flags, silent_flet_updates):
    screen = _start("off")
    _check(screen, "keep SB in line")
    assert screen.exampleText.visible is False


@pytest.mark.parametrize("mode", ["hint", "after_check"])
def test_retry_restores_blank_gaps(
    isolated_csv_dir, restore_flags, silent_flet_updates, mode
):
    screen = _start(mode)
    _check(screen, "nope")
    assert screen._get_check_button_text() == "Try again"
    assert _shown_text(screen) == "I keep him in line."

    screen.on_check_click(SimpleNamespace())

    assert screen._get_check_button_text() == "Check"
    assert screen.exampleText.visible is True
    assert _shown_text(screen) == "I _____ him _____."

    _check(screen, "keep SB in line")
    assert screen._get_check_button_text() == "Next"
    assert _shown_text(screen) == "I keep him in line."


@pytest.mark.parametrize("typed", ["keep in line", "keeps, in line", "keep in; line"])
def test_hint_accepts_gap_answers_and_shows_the_word(
    isolated_csv_dir, restore_flags, silent_flet_updates, typed
):
    screen = _start("hint")
    _check(screen, typed)

    assert screen._get_check_button_text() == "Next"
    assert screen.word.value == "keep SB in line"


def test_after_check_does_not_accept_gap_answers(
    isolated_csv_dir, restore_flags, silent_flet_updates
):
    screen = _start("after_check")
    _check(screen, "keep in line")
    assert screen._get_check_button_text() == "Try again"


def test_card_without_example_shows_nothing_in_hint(
    isolated_csv_dir, restore_flags, silent_flet_updates
):
    screen = _start("hint", example="")
    assert screen.exampleText.visible is False
    _check(screen, "keep in line")
    assert screen._get_check_button_text() == "Try again"
    assert screen.exampleText.visible is False


def test_set_override_wins_over_app_mode(
    isolated_csv_dir, restore_flags, silent_flet_updates
):
    from learning_app.ui.components.word_definition_field import WordDefinitionField

    _save_set("I {keep} him {in line}.")
    LearnPreferences.example_mode = "off"
    enable_set_overrides(FILE_NAME)
    set_override_value(FILE_NAME, FilesColumns.EXAMPLE_MODE.value, "hint")
    TtsPreferences.auto_speak_definitions = False
    screen = WordDefinitionField(FILE_NAME, session=True)
    screen.start()

    assert _shown_text(screen) == "I _____ him _____."
