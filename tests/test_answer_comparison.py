"""Tests for learn-session answer comparison.

Word-formation fields and definition answers both grade typed text with
``WordField.contain_word``. A slash in the stored answer separates
alternatives. A slash in the typed answer lists forms, and every form must be
one of those alternatives. Grading lowercases both sides and ignores leading
and trailing spaces around each form. ``STH`` and ``SB`` are ordinary text.
Spaces around ``/`` belong to the separator, so ``STH / SB`` and ``STH/SB``
are the same two answers. Punctuation and spaces inside a phrase are kept.
"""

from types import SimpleNamespace

import pandas as pd
import pytest

from learning_app.data.app_data import generate_empty_files_data, save_set
from learning_app.data.constants import PartsOfSpeech, StatsColumns, WordDefinitions
from learning_app.ui.components.controls import WordField
from learning_app.ui.learn_preferences import LearnPreferences
from learning_app.ui.tts_preferences import TtsPreferences

# Stored cell from the report, plus the same cell with the separator spaces removed.
RELY_EXPECTED = ("to rely on STH / SB", "to rely on STH/SB")
# Trimmed slash sides. The right-hand answer is the segment after "/", "SB",
# not the prefix repeated as "to rely on SB". Case and outer spaces follow grading.
RELY_ACCEPTED = (
    "to rely on STH",
    "to rely on sth",
    "  to rely on STH  ",
    "SB",
    "sb",
    "  sb  ",
)
RELY_REJECTED = (
    "to depend on somebody",
    "not this phrase",
    "",
)

PLACEHOLDER_EXPECTED = ("STH / SB", "STH/SB")
PLACEHOLDER_ACCEPTED = (
    "STH",
    "sth",
    "  STH  ",
    "SB",
    "sb",
    "  sb  ",
)
PLACEHOLDER_REJECTED = (
    "something",
    "somebody",
    "to rely on STH",
)


def _is_correct(expected: str, typed: str) -> bool:
    field = WordField(label="answer", read_only=False)
    field.value = typed
    return field.contain_word(expected)


def _grade_label(correct: bool) -> str:
    return "correct" if correct else "wrong"


def _mismatch(expected: str, typed: str, actual: bool, wanted: bool) -> str:
    return (
        f"input={typed!r} expected_answer={expected!r} "
        f"expected_grade={_grade_label(wanted)} actual_grade={_grade_label(actual)}"
    )


def _assert_grade(expected: str, typed: str, wanted: bool) -> None:
    actual = _is_correct(expected, typed)
    assert actual is wanted, _mismatch(expected, typed, actual, wanted)


@pytest.fixture
def restore_flags():
    retry = LearnPreferences.retry_until_correct
    auto_speak = TtsPreferences.auto_speak_definitions
    yield
    LearnPreferences.retry_until_correct = retry
    TtsPreferences.auto_speak_definitions = auto_speak


@pytest.fixture
def silent_flet_updates(monkeypatch):
    monkeypatch.setattr("flet.Control.update", lambda self: None, raising=False)


def test_slash_alternatives_ignore_case_and_outer_space():
    _assert_grade("go/goes/went", "go", True)
    _assert_grade("go/goes/went", "GO", True)
    _assert_grade("go/goes/went", "  went  ", True)
    _assert_grade("go/goes/went", "going", False)
    _assert_grade("to rely on STH", "  TO RELY ON sth  ", True)


def test_punctuation_and_inner_spaces_stay_significant():
    _assert_grade("go", "go.", False)
    _assert_grade("to rely on STH", "to rely on STH.", False)
    _assert_grade("to rely on STH", "to  rely on STH", False)


def test_joined_slash_text_passes_when_every_form_is_stored():
    _assert_grade("go/goes/went", "go/goes/went", True)
    _assert_grade("go/goes/went", "go / goes / went", True)


FORMS = "go/goes/went/gone"
FORMS_ACCEPTED = (
    "goes/went",
    "go /gone",
    "go/goes/ went / gone",
    "gone/go",
    "go/go",
)
FORMS_REJECTED = (
    "goes/wend",
    "go/",
    "go//gone",
    "/",
    "go /",
)


@pytest.mark.parametrize("typed", FORMS_ACCEPTED)
def test_typed_slash_forms_pass_when_each_piece_is_stored(typed):
    _assert_grade(FORMS, typed, True)


@pytest.mark.parametrize("typed", FORMS_REJECTED)
def test_typed_slash_forms_fail_on_unknown_or_empty_piece(typed):
    _assert_grade(FORMS, typed, False)


def test_rely_phrase_accepts_full_typed_slash_phrase():
    expected = "to rely on STH / SB"
    _assert_grade(expected, "to rely on STH / SB", True)
    _assert_grade(expected, "to rely on STH", True)
    _assert_grade(expected, "SB", True)
    _assert_grade(expected, "to rely on STH / something", False)
    _assert_grade(expected, "to  rely on STH", False)
    _assert_grade(expected, "to  rely on STH / SB", False)


def test_spaced_rely_phrase_has_an_acceptable_typing():
    expected = "to rely on STH / SB"
    grades = {typed: _is_correct(expected, typed) for typed in RELY_ACCEPTED}
    assert any(grades.values()), "; ".join(
        _mismatch(expected, typed, actual, True) for typed, actual in grades.items()
    )


@pytest.mark.parametrize("expected", RELY_EXPECTED)
@pytest.mark.parametrize("typed", RELY_ACCEPTED)
def test_rely_phrase_accepts_each_slash_side(expected, typed):
    _assert_grade(expected, typed, True)


@pytest.mark.parametrize("expected", RELY_EXPECTED)
@pytest.mark.parametrize("typed", RELY_REJECTED)
def test_rely_phrase_rejects_unrelated_answers(expected, typed):
    _assert_grade(expected, typed, False)


@pytest.mark.parametrize("expected", PLACEHOLDER_EXPECTED)
@pytest.mark.parametrize("typed", PLACEHOLDER_ACCEPTED)
def test_placeholder_slash_spacing_and_case(expected, typed):
    _assert_grade(expected, typed, True)


@pytest.mark.parametrize("expected", PLACEHOLDER_EXPECTED)
@pytest.mark.parametrize("typed", PLACEHOLDER_REJECTED)
def test_placeholder_pair_rejects_other_phrases(expected, typed):
    _assert_grade(expected, typed, False)


def _save_definition_set(word: str, file_name: str) -> str:
    generate_empty_files_data()
    save_set(
        pd.DataFrame(
            {
                WordDefinitions.DEFINITION.value: ["count on a person or thing"],
                WordDefinitions.WORD.value: [word],
                StatsColumns.CORRECT_ANSWERS.value: [0],
                StatsColumns.GOOD_ANSWERS_IN_A_ROW.value: [False],
                StatsColumns.GOOD_ANSWER.value: [False],
                StatsColumns.WORD_TO_LEARN.value: [False],
            }
        ),
        file_name,
    )
    return file_name


def _start_definition_session(file_name: str):
    from learning_app.ui.components.word_definition_field import WordDefinitionField

    TtsPreferences.auto_speak_definitions = False
    screen = WordDefinitionField(file_name, session=True)
    screen.start()
    return screen


@pytest.mark.parametrize("typed", ("to rely on STH", "sb"))
def test_retry_until_correct_accepts_rely_phrase(
    isolated_csv_dir, restore_flags, silent_flet_updates, typed
):
    expected = "to rely on STH / SB"
    file_name = _save_definition_set(expected, "rely_definitions.csv")
    LearnPreferences.retry_until_correct = True
    screen = _start_definition_session(file_name)

    screen.word.value = "nope"
    screen.on_check_click(SimpleNamespace())
    assert screen._get_check_button_text() == "Try again"
    screen.on_check_click(SimpleNamespace())
    assert screen._get_check_button_text() == "Check"
    assert screen.word.value == ""

    screen.word.value = typed
    screen.on_check_click(SimpleNamespace())
    assert screen._get_check_button_text() == "Next", _mismatch(
        expected, typed, False, True
    )
    assert screen._retrying_after_wrong is False


def test_word_formation_check_accepts_rely_phrase(
    isolated_csv_dir, restore_flags, silent_flet_updates
):
    from learning_app.ui.components.word_fields import WordFields

    expected = "to rely on STH / SB"
    typed = "to rely on STH"
    generate_empty_files_data()
    save_set(
        pd.DataFrame(
            {
                PartsOfSpeech.VERB.value: [expected],
                PartsOfSpeech.PERSON.value: ["reliant"],
                PartsOfSpeech.THING.value: ["reliance"],
                PartsOfSpeech.ADJECTIVE.value: ["reliable"],
                PartsOfSpeech.ADVERB.value: ["reliably"],
                StatsColumns.CORRECT_ANSWERS.value: [0],
                StatsColumns.GOOD_ANSWERS_IN_A_ROW.value: [False],
                StatsColumns.GOOD_ANSWER.value: [False],
                StatsColumns.WORD_TO_LEARN.value: [False],
            }
        ),
        "rely_words.csv",
    )
    LearnPreferences.retry_until_correct = True
    TtsPreferences.auto_speak_definitions = False
    screen = WordFields("rely_words.csv", session=True)
    screen.start()
    answers = {
        "verb": typed,
        "person": "reliant",
        "thing": "reliance",
        "adjective": "reliable",
        "adverb": "reliably",
    }
    for column_name, field in screen.dict_word_fields.items():
        field.value = answers[column_name]

    screen.on_check_click(SimpleNamespace())
    assert screen._get_check_button_text() == "Next", _mismatch(
        expected, typed, False, True
    )
