"""Tests for retry-until-correct learn-session Check / Try again loop."""

from types import SimpleNamespace

import pandas as pd
import pytest

from learning_app.data.app_data import generate_empty_files_data, load_set, save_set
from learning_app.data.constants import PartsOfSpeech, StatsColumns, WordDefinitions
from learning_app.ui.learn_preferences import LearnPreferences
from learning_app.ui.tts_preferences import TtsPreferences


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


def _stats_row(path_name: str) -> pd.Series:
    loaded = load_set(path_name)
    return loaded.loc[0]


def _save_definition_set(file_name: str = "retry_definitions.csv") -> str:
    generate_empty_files_data()
    save_set(
        pd.DataFrame(
            {
                WordDefinitions.DEFINITION.value: ["a path"],
                WordDefinitions.WORD.value: ["way"],
                StatsColumns.CORRECT_ANSWERS.value: [0],
                StatsColumns.GOOD_ANSWERS_IN_A_ROW.value: [False],
                StatsColumns.GOOD_ANSWER.value: [False],
                StatsColumns.WORD_TO_LEARN.value: [False],
            }
        ),
        file_name,
    )
    return file_name


def _save_words_set(file_name: str = "retry_words.csv") -> str:
    generate_empty_files_data()
    save_set(
        pd.DataFrame(
            {
                PartsOfSpeech.VERB.value: ["go"],
                PartsOfSpeech.PERSON.value: ["walker"],
                PartsOfSpeech.THING.value: ["path"],
                PartsOfSpeech.ADJECTIVE.value: ["quick"],
                PartsOfSpeech.ADVERB.value: ["quickly"],
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


def test_wrong_check_with_retry_on_shows_try_again(
    isolated_csv_dir, restore_flags, silent_flet_updates
):
    file_name = _save_definition_set()
    LearnPreferences.retry_until_correct = True
    screen = _start_definition_session(file_name)
    good_calls: list[bool] = []
    bad_calls: list[bool] = []
    screen.words.good_answer_at_current_row = lambda: good_calls.append(True)
    original_bad = screen.words.bad_answer_at_current_row

    def tracked_bad():
        bad_calls.append(True)
        original_bad()

    screen.words.bad_answer_at_current_row = tracked_bad
    screen.word.value = "nope"
    screen.on_check_click(SimpleNamespace())

    assert screen._get_check_button_text() == "Try again"
    assert screen._retrying_after_wrong is True
    assert screen._answer_is_revealed() is True
    assert screen._speak_unlocked is True
    assert bad_calls == [True]
    assert good_calls == []
    assert screen.pb.current_qty == 1
    stats = _stats_row(file_name)
    assert bool(stats[StatsColumns.GOOD_ANSWER.value]) is False
    assert bool(stats[StatsColumns.WORD_TO_LEARN.value]) is True
    assert int(stats[StatsColumns.CORRECT_ANSWERS.value]) == 0


def test_retry_wrong_check_does_not_change_stats(
    isolated_csv_dir, restore_flags, silent_flet_updates
):
    file_name = _save_definition_set()
    LearnPreferences.retry_until_correct = True
    screen = _start_definition_session(file_name)
    good_calls: list[bool] = []
    bad_calls: list[bool] = []
    screen.words.good_answer_at_current_row = lambda: good_calls.append(True)
    original_bad = screen.words.bad_answer_at_current_row

    def tracked_bad():
        bad_calls.append(True)
        original_bad()

    screen.words.bad_answer_at_current_row = tracked_bad
    screen.word.value = "nope"
    screen.on_check_click(SimpleNamespace())
    screen.on_check_click(SimpleNamespace())
    assert screen._get_check_button_text() == "Check"
    assert screen.word.value == ""
    assert screen._speak_unlocked is False

    screen.word.value = "still-wrong"
    screen.on_check_click(SimpleNamespace())

    assert screen._get_check_button_text() == "Try again"
    assert bad_calls == [True]
    assert good_calls == []
    assert screen.pb.current_qty == 1
    stats = _stats_row(file_name)
    assert int(stats[StatsColumns.CORRECT_ANSWERS.value]) == 0
    assert bool(stats[StatsColumns.GOOD_ANSWER.value]) is False
    assert bool(stats[StatsColumns.WORD_TO_LEARN.value]) is True


def test_correct_retry_shows_next_without_good_stats(
    isolated_csv_dir, restore_flags, silent_flet_updates
):
    file_name = _save_definition_set()
    LearnPreferences.retry_until_correct = True
    screen = _start_definition_session(file_name)
    good_calls: list[bool] = []
    screen.words.good_answer_at_current_row = lambda: good_calls.append(True)
    screen.word.value = "nope"
    screen.on_check_click(SimpleNamespace())
    screen.on_check_click(SimpleNamespace())
    screen.word.value = "way"
    screen.on_check_click(SimpleNamespace())

    assert screen._get_check_button_text() == "Next"
    assert screen._retrying_after_wrong is False
    assert screen._speak_unlocked is True
    assert good_calls == []
    stats = _stats_row(file_name)
    assert int(stats[StatsColumns.CORRECT_ANSWERS.value]) == 0
    assert bool(stats[StatsColumns.GOOD_ANSWER.value]) is False
    assert bool(stats[StatsColumns.WORD_TO_LEARN.value]) is True


def test_retry_off_still_goes_next_after_wrong(
    isolated_csv_dir, restore_flags, silent_flet_updates
):
    file_name = _save_definition_set()
    LearnPreferences.retry_until_correct = False
    screen = _start_definition_session(file_name)
    screen.word.value = "nope"
    screen.on_check_click(SimpleNamespace())

    assert screen._get_check_button_text() == "Next"
    assert screen._retrying_after_wrong is False
    stats = _stats_row(file_name)
    assert bool(stats[StatsColumns.WORD_TO_LEARN.value]) is True


def test_first_correct_check_still_records_good_answer(
    isolated_csv_dir, restore_flags, silent_flet_updates
):
    file_name = _save_definition_set()
    LearnPreferences.retry_until_correct = True
    screen = _start_definition_session(file_name)
    screen.word.value = "way"
    screen.on_check_click(SimpleNamespace())

    assert screen._get_check_button_text() == "Next"
    stats = _stats_row(file_name)
    assert int(stats[StatsColumns.CORRECT_ANSWERS.value]) == 1
    assert bool(stats[StatsColumns.GOOD_ANSWER.value]) is True


def test_words_prepare_retry_keeps_prompt(
    isolated_csv_dir, restore_flags, silent_flet_updates
):
    from learning_app.ui.components.word_fields import WordFields

    file_name = _save_words_set()
    LearnPreferences.retry_until_correct = True
    TtsPreferences.auto_speak_definitions = False
    screen = WordFields(file_name, session=True)
    screen.start()
    prompt = screen.Word.value
    for field in screen.dict_word_fields.values():
        if not field.disabled:
            field.value = "wrong"
    screen.on_check_click(SimpleNamespace())
    assert screen._get_check_button_text() == "Try again"
    screen.on_check_click(SimpleNamespace())

    assert screen.Word.value == prompt
    assert screen._get_check_button_text() == "Check"
    enabled = [field for field in screen.dict_word_fields.values() if not field.disabled]
    assert enabled
    assert all(field.value == "" for field in enabled)


def test_words_prepare_retry_keeps_correct_fields(
    isolated_csv_dir, restore_flags, silent_flet_updates
):
    from learning_app.ui.components.word_fields import WordFields

    file_name = _save_words_set()
    LearnPreferences.retry_until_correct = True
    TtsPreferences.auto_speak_definitions = False
    screen = WordFields(file_name, session=True)
    screen.start()

    answers = {
        "verb": "go",
        "person": "walker",
        "thing": "path",
        "adjective": "quick",
        "adverb": "quickly",
    }
    for column_name, field in screen.dict_word_fields.items():
        if field.disabled:
            continue
        field.value = answers[column_name] if column_name == "verb" else "wrong"

    screen.on_check_click(SimpleNamespace())
    assert screen._get_check_button_text() == "Try again"
    screen.on_check_click(SimpleNamespace())

    assert screen._get_check_button_text() == "Check"
    assert screen.verbWord.value == "go"
    assert screen.verbWord.read_only is True
    assert screen.verbWord.is_indicated_correct() is True
    for column_name, field in screen.dict_word_fields.items():
        if field.disabled or column_name == "verb":
            continue
        assert field.value == ""
        assert field.read_only is False

    for column_name, field in screen.dict_word_fields.items():
        if field.disabled or column_name == "verb":
            continue
        field.value = answers[column_name]
    screen.on_check_click(SimpleNamespace())

    assert screen._get_check_button_text() == "Next"
    assert screen.verbWord.is_indicated_correct() is True
    stats = _stats_row(file_name)
    assert int(stats[StatsColumns.CORRECT_ANSWERS.value]) == 0
    assert bool(stats[StatsColumns.WORD_TO_LEARN.value]) is True
