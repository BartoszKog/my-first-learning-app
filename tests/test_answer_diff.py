"""Tests for the wrong-answer letter diff and its learn-screen feedback.

``diff_answer`` splits the typed text into ``same`` and ``wrong`` runs and
inserts ``missing`` runs from the closest stored alternative. After a wrong,
non-blank Check, ``WordField.feedback`` shows those runs under the field.
Blank and correct answers show nothing, and Try again or Next hides it.
"""

from types import SimpleNamespace

import pandas as pd
import pytest

from learning_app.data.answer_diff import (
    CLOSE_MATCH_RATIO,
    DiffPiece,
    closest_alternative,
    diff_answer,
)
from learning_app.data.app_data import generate_empty_files_data, save_set
from learning_app.data.constants import PartsOfSpeech, StatsColumns, WordDefinitions
from learning_app.ui.components.controls import WordField
from learning_app.ui.learn_preferences import LearnPreferences
from learning_app.ui.tts_preferences import TtsPreferences


def _kinds(pieces):
    return [(piece.kind, piece.text) for piece in pieces]


def _typed_back(pieces):
    return "".join(piece.text for piece in pieces if piece.kind != "missing")


def _expected_back(pieces):
    return "".join(piece.text for piece in pieces if piece.kind != "wrong")


def test_swapped_letters_mark_wrong_and_missing():
    pieces, ratio = diff_answer("recieve", "receive")
    assert _typed_back(pieces) == "recieve"
    assert _expected_back(pieces) == "receive"
    assert {piece.kind for piece in pieces} == {"same", "wrong", "missing"}
    assert ratio >= CLOSE_MATCH_RATIO


def test_missing_letter_is_inserted():
    pieces, _ = diff_answer("recive", "receive")
    assert _kinds(pieces) == [("same", "rec"), ("missing", "e"), ("same", "ive")]


def test_extra_letter_is_wrong():
    pieces, _ = diff_answer("receeive", "receive")
    assert _kinds(pieces) == [("same", "rece"), ("wrong", "e"), ("same", "ive")]


def test_replaced_letter_is_wrong_then_missing():
    pieces, _ = diff_answer("walk", "wall")
    assert _kinds(pieces) == [("same", "wal"), ("wrong", "k"), ("missing", "l")]


def test_case_is_ignored_but_spelling_is_kept():
    pieces, _ = diff_answer("  RECive ", "receive")
    assert _kinds(pieces) == [("same", "REC"), ("missing", "e"), ("same", "ive")]


def test_closest_slash_alternative_is_used():
    assert closest_alternative("gose", "go/goes/went") == "goes"
    pieces, _ = diff_answer("gose", "go / goes / went")
    assert _expected_back(pieces) == "goes"


def test_typed_slash_forms_are_diffed_separately():
    pieces, _ = diff_answer("gose/wnt", "go/goes/went")
    assert DiffPiece("same", " / w") in pieces
    assert _expected_back(pieces) == "goes / went"


def test_unrelated_word_is_below_close_ratio():
    _, ratio = diff_answer("banana", "receive")
    assert ratio < CLOSE_MATCH_RATIO


def test_blank_typed_gives_no_pieces():
    assert diff_answer("   ", "receive") == ([], 0.0)


@pytest.fixture
def silent_flet_updates(monkeypatch):
    monkeypatch.setattr("flet.Control.update", lambda self: None, raising=False)


def _feedback_text(field: WordField) -> str:
    if field.feedback.spans:
        return "".join(span.text for span in field.feedback.spans)
    return field.feedback.value or ""


def _bad_field(typed: str, expected: str) -> WordField:
    field = WordField(label="answer", read_only=False)
    field.value = typed
    field.indicate_bad_answer(expected)
    return field


def test_wrong_answer_shows_marked_typed_text(silent_flet_updates):
    field = _bad_field("recieve", "receive")
    assert field.value == "receive"
    assert field.feedback.visible is True
    assert _feedback_text(field).startswith("Your answer: ")
    styled = [span for span in field.feedback.spans if span.style is not None]
    assert any(span.style.decoration is not None for span in styled)


def test_unrelated_wrong_answer_shows_plain_text(silent_flet_updates):
    field = _bad_field("banana", "receive")
    assert field.feedback.visible is True
    assert field.feedback.spans == []
    assert field.feedback.value == "Your answer: banana"


def test_blank_wrong_answer_shows_nothing(silent_flet_updates):
    field = _bad_field("  ", "receive")
    assert field.feedback.visible is False


def test_good_answer_and_reset_hide_feedback(silent_flet_updates):
    field = _bad_field("recieve", "receive")
    field.reset()
    assert field.feedback.visible is False
    field.value = "receive"
    field.indicate_good_answer("receive")
    assert field.feedback.visible is False


@pytest.fixture
def restore_flags():
    retry = LearnPreferences.retry_until_correct
    auto_speak = TtsPreferences.auto_speak_definitions
    yield
    LearnPreferences.retry_until_correct = retry
    TtsPreferences.auto_speak_definitions = auto_speak


def _start_definition_session(word: str):
    from learning_app.ui.components.word_definition_field import WordDefinitionField

    generate_empty_files_data()
    save_set(
        pd.DataFrame(
            {
                WordDefinitions.DEFINITION.value: ["to get something"],
                WordDefinitions.WORD.value: [word],
                StatsColumns.CORRECT_ANSWERS.value: [0],
                StatsColumns.GOOD_ANSWERS_IN_A_ROW.value: [False],
                StatsColumns.GOOD_ANSWER.value: [False],
                StatsColumns.WORD_TO_LEARN.value: [False],
            }
        ),
        "diff_definitions.csv",
    )
    TtsPreferences.auto_speak_definitions = False
    screen = WordDefinitionField("diff_definitions.csv", session=True)
    screen.start()
    return screen


def test_definition_feedback_sits_between_field_and_buttons(
    isolated_csv_dir, restore_flags, silent_flet_updates
):
    screen = _start_definition_session("receive")
    controls = screen.active_controls
    assert controls.index(screen.word.feedback) == controls.index(screen.word) + 1
    assert controls.index(screen.check_row) == controls.index(screen.word.feedback) + 1


def test_definition_wrong_check_then_try_again(
    isolated_csv_dir, restore_flags, silent_flet_updates
):
    LearnPreferences.retry_until_correct = True
    screen = _start_definition_session("receive")
    assert screen.word.feedback.visible is False

    screen.word.value = "recieve"
    screen.on_check_click(SimpleNamespace())
    assert screen._get_check_button_text() == "Try again"
    assert screen.word.value == "receive"
    assert screen.word.feedback.visible is True
    assert "Your answer: " in _feedback_text(screen.word)

    screen.on_check_click(SimpleNamespace())
    assert screen._get_check_button_text() == "Check"
    assert screen.word.feedback.visible is False


def test_definition_blank_and_correct_checks_show_nothing(
    isolated_csv_dir, restore_flags, silent_flet_updates
):
    LearnPreferences.retry_until_correct = True
    screen = _start_definition_session("receive")
    screen.word.value = ""
    screen.on_check_click(SimpleNamespace())
    assert screen._get_check_button_text() == "Try again"
    assert screen.word.feedback.visible is False

    screen.on_check_click(SimpleNamespace())
    screen.word.value = "Receive"
    screen.on_check_click(SimpleNamespace())
    assert screen._get_check_button_text() == "Next"
    assert screen.word.feedback.visible is False


def test_word_formation_feedback_only_on_wrong_typed_fields(
    isolated_csv_dir, restore_flags, silent_flet_updates
):
    from learning_app.ui.components.word_fields import WordFields

    generate_empty_files_data()
    save_set(
        pd.DataFrame(
            {
                PartsOfSpeech.VERB.value: ["receive"],
                PartsOfSpeech.PERSON.value: ["receiver"],
                PartsOfSpeech.THING.value: ["reception"],
                PartsOfSpeech.ADJECTIVE.value: ["receptive"],
                PartsOfSpeech.ADVERB.value: ["receptively"],
                StatsColumns.CORRECT_ANSWERS.value: [0],
                StatsColumns.GOOD_ANSWERS_IN_A_ROW.value: [False],
                StatsColumns.GOOD_ANSWER.value: [False],
                StatsColumns.WORD_TO_LEARN.value: [False],
            }
        ),
        "diff_words.csv",
    )
    LearnPreferences.retry_until_correct = True
    TtsPreferences.auto_speak_definitions = False
    screen = WordFields("diff_words.csv", session=True)
    screen.start()

    for word_field in screen.dict_word_fields.values():
        index = screen.active_controls.index(word_field)
        assert screen.active_controls[index + 1] is word_field.feedback

    screen.verbWord.value = "receive"
    screen.nounPersonWord.value = "reciever"
    screen.nounThingWord.value = ""
    screen.adjWord.value = "receptiv"
    screen.advWord.value = "   "
    screen.on_check_click(SimpleNamespace())

    assert screen._get_check_button_text() == "Try again"
    assert screen.verbWord.feedback.visible is False
    assert screen.nounPersonWord.feedback.visible is True
    assert screen.nounThingWord.feedback.visible is False
    assert screen.adjWord.feedback.visible is True
    assert screen.advWord.feedback.visible is False

    screen.on_check_click(SimpleNamespace())
    assert all(not field.feedback.visible for field in screen.dict_word_fields.values())
