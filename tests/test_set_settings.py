"""Per-set overrides in files.csv and the set-settings screen."""

from types import SimpleNamespace

import pandas as pd
import pytest

from learning_app.data.app_data import (
    AppData,
    add_new_file,
    ensure_files_catalog_columns,
    generate_empty_files_data,
    save_set,
)
from learning_app.data.constants import FilesColumns, PartsOfSpeech, StatsColumns
from learning_app.data.set_settings import (
    clear_set_overrides,
    effective_set_settings,
    enable_set_overrides,
    read_override_cells,
    set_override_value,
)
from learning_app.ui.learn_preferences import LearnPreferences
from learning_app.ui.tts_preferences import TtsPreferences


@pytest.fixture
def restore_preferences():
    language = TtsPreferences.language
    auto_speak = TtsPreferences.auto_speak_definitions
    formations = TtsPreferences.speakers_word_formations
    word = TtsPreferences.speakers_word
    definition = TtsPreferences.speakers_definition
    retry = LearnPreferences.retry_until_correct
    words_queue = LearnPreferences.word_formations_queue_size
    definitions_queue = LearnPreferences.definitions_queue_size
    yield
    TtsPreferences.language = language
    TtsPreferences.auto_speak_definitions = auto_speak
    TtsPreferences.speakers_word_formations = formations
    TtsPreferences.speakers_word = word
    TtsPreferences.speakers_definition = definition
    LearnPreferences.retry_until_correct = retry
    LearnPreferences.word_formations_queue_size = words_queue
    LearnPreferences.definitions_queue_size = definitions_queue


def _words_frame(count: int) -> pd.DataFrame:
    return pd.DataFrame(
        {
            PartsOfSpeech.VERB.value: [f"verb{i}" for i in range(count)],
            PartsOfSpeech.PERSON.value: [f"person{i}" for i in range(count)],
            PartsOfSpeech.THING.value: [f"thing{i}" for i in range(count)],
            PartsOfSpeech.ADJECTIVE.value: [f"adj{i}" for i in range(count)],
            PartsOfSpeech.ADVERB.value: [f"adv{i}" for i in range(count)],
            StatsColumns.CORRECT_ANSWERS.value: [0] * count,
            StatsColumns.GOOD_ANSWERS_IN_A_ROW.value: [False] * count,
            StatsColumns.GOOD_ANSWER.value: [False] * count,
            StatsColumns.WORD_TO_LEARN.value: [False] * count,
        }
    )


def test_catalog_migration_adds_empty_override_columns(isolated_csv_dir):
    catalog = isolated_csv_dir / "files.csv"
    catalog.write_text(
        "file_name,title,subtitle,created_at,last_used,use_count\n"
        "Animals_words.csv,Animals,,2000-01-01T00:00:00+00:00,,0\n",
        encoding="utf-8",
    )

    frame = ensure_files_catalog_columns()

    for column in (
        FilesColumns.TTS_LANGUAGE.value,
        FilesColumns.TTS_AUTO_SPEAK.value,
        FilesColumns.SPEAKERS_WORD_FORMATIONS.value,
        FilesColumns.SPEAKERS_WORD.value,
        FilesColumns.SPEAKERS_DEFINITION.value,
        FilesColumns.RETRY_UNTIL_CORRECT.value,
        FilesColumns.QUEUE_SIZE.value,
    ):
        assert column in frame.columns
        assert read_override_cells("Animals_words.csv")[column] == ""
    stored = catalog.read_text(encoding="utf-8")
    assert "tts_language" in stored
    assert "true" not in stored
    assert "false" not in stored


def test_empty_cells_inherit_and_false_is_stored(isolated_csv_dir, restore_preferences):
    generate_empty_files_data()
    add_new_file("alpha_words.csv", "Alpha")
    TtsPreferences.language = "de"
    TtsPreferences.speakers_word_formations = True
    LearnPreferences.retry_until_correct = True
    LearnPreferences.word_formations_queue_size = 8

    inherited = effective_set_settings("alpha_words.csv")
    assert inherited.uses_app_defaults is True
    assert inherited.language == "de"
    assert inherited.retry_until_correct is True
    assert inherited.queue_size == 8
    assert inherited.speakers_word_formations is True

    enable_set_overrides("alpha_words.csv")
    set_override_value("alpha_words.csv", FilesColumns.RETRY_UNTIL_CORRECT.value, "false")
    set_override_value("alpha_words.csv", FilesColumns.QUEUE_SIZE.value, "6")
    set_override_value("alpha_words.csv", FilesColumns.TTS_LANGUAGE.value, "pl")
    LearnPreferences.retry_until_correct = True
    LearnPreferences.word_formations_queue_size = 4
    TtsPreferences.language = "en"

    custom = effective_set_settings("alpha_words.csv")
    assert custom.uses_app_defaults is False
    assert custom.retry_until_correct is False
    assert custom.queue_size == 6
    assert custom.language == "pl"
    cells = read_override_cells("alpha_words.csv")
    assert cells[FilesColumns.RETRY_UNTIL_CORRECT.value] == "false"
    assert cells[FilesColumns.TTS_AUTO_SPEAK.value] == ""
    assert cells[FilesColumns.SPEAKERS_WORD.value] == ""
    assert cells[FilesColumns.SPEAKERS_DEFINITION.value] == ""

    assert effective_set_settings("alpha_words.csv").queue_size == 6
    set_override_value("alpha_words.csv", FilesColumns.QUEUE_SIZE.value, "99")
    assert effective_set_settings("alpha_words.csv").queue_size == 10
    set_override_value("alpha_words.csv", FilesColumns.QUEUE_SIZE.value, "nope")
    assert effective_set_settings("alpha_words.csv").queue_size == 4

    clear_set_overrides("alpha_words.csv")
    cleared = read_override_cells("alpha_words.csv")
    assert all(value == "" for value in cleared.values())
    assert effective_set_settings("alpha_words.csv").uses_app_defaults is True
    assert effective_set_settings("alpha_words.csv").language == "en"


def test_draw_index_group_uses_set_queue_size(isolated_csv_dir, restore_preferences):
    generate_empty_files_data()
    save_set(_words_frame(12), "queue_words.csv")
    add_new_file("queue_words.csv", "Queue")
    LearnPreferences.word_formations_queue_size = 4

    words = AppData("queue_words.csv")
    assert len(words.current_group_of_indexes) == 4

    enable_set_overrides("queue_words.csv")
    set_override_value("queue_words.csv", FilesColumns.QUEUE_SIZE.value, "6")

    assert words.draw_index_group() == 6
    assert len(words.current_group_of_indexes) == 6


def test_set_settings_checkbox_clears_columns(isolated_csv_dir, restore_preferences):
    from learning_app.ui.screens.set_settings_menu import SetSettingsMenu

    generate_empty_files_data()
    add_new_file("alpha_words.csv", "Alpha")
    add_new_file("beta_definitions.csv", "Beta")
    TtsPreferences.language = "de"
    TtsPreferences.speakers_word_formations = True
    LearnPreferences.retry_until_correct = True
    LearnPreferences.word_formations_queue_size = 7
    LearnPreferences.definitions_queue_size = 12

    words_screen = SetSettingsMenu("alpha_words.csv", width=300)
    assert words_screen.kind_text.value == "Word formations"
    assert words_screen.use_app_settings_switch.value is True
    assert words_screen.language_dropdown.disabled is True
    assert words_screen.language_dropdown.value == "de"
    assert words_screen.auto_speak_switch is None
    assert words_screen.speakers_word_switch is None
    assert words_screen.speakers_definition_switch is None
    assert words_screen.speakers_word_formations_switch is not None
    assert words_screen.speakers_word_formations_switch.disabled is True
    assert words_screen.queue_slider.slider.min == 3
    assert words_screen.queue_slider.slider.max == 10
    assert words_screen.queue_slider.slider.disabled is True

    words_screen.use_app_settings_switch.value = False
    words_screen.on_use_app_settings_change(
        SimpleNamespace(control=words_screen.use_app_settings_switch)
    )
    stored = read_override_cells("alpha_words.csv")
    assert stored[FilesColumns.TTS_LANGUAGE.value] == "de"
    assert stored[FilesColumns.QUEUE_SIZE.value] == "7"
    assert stored[FilesColumns.RETRY_UNTIL_CORRECT.value] == "true"
    assert stored[FilesColumns.SPEAKERS_WORD_FORMATIONS.value] == "true"
    assert stored[FilesColumns.TTS_AUTO_SPEAK.value] == ""
    assert stored[FilesColumns.SPEAKERS_WORD.value] == ""
    assert stored[FilesColumns.SPEAKERS_DEFINITION.value] == ""
    assert words_screen.language_dropdown.disabled is False

    words_screen.language_dropdown.value = "pl"
    words_screen.on_language_select(SimpleNamespace(control=words_screen.language_dropdown))
    assert read_override_cells("alpha_words.csv")[FilesColumns.TTS_LANGUAGE.value] == "pl"

    words_screen.use_app_settings_switch.value = True
    words_screen.on_use_app_settings_change(
        SimpleNamespace(control=words_screen.use_app_settings_switch)
    )
    cleared = read_override_cells("alpha_words.csv")
    assert all(value == "" for value in cleared.values())
    assert words_screen.language_dropdown.disabled is True
    assert words_screen.language_dropdown.value == "de"
    assert words_screen.queue_slider.slider.disabled is True

    definitions = SetSettingsMenu("beta_definitions.csv", width=300)
    assert definitions.kind_text.value == "Definitions"
    assert definitions.auto_speak_switch is not None
    assert definitions.speakers_word_switch is not None
    assert definitions.speakers_definition_switch is not None
    assert definitions.speakers_word_formations_switch is None
    assert definitions.queue_slider.slider.min == 4
    assert definitions.queue_slider.slider.max == 15
    assert "Set settings" in definitions.heading.value
