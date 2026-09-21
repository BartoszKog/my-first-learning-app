"""Tests for TTS preference defaults and Settings wiring."""

from types import SimpleNamespace

import flet as ft
import pytest

from learning_app.ui.tts_preferences import (
    DEFAULT_LANGUAGE,
    LANGUAGE_CODES,
    TtsPreferences,
)


@pytest.fixture
def restore_tts_preferences():
    language = TtsPreferences.language
    auto_speak = TtsPreferences.auto_speak_definitions
    formations = TtsPreferences.speakers_word_formations
    word = TtsPreferences.speakers_word
    definition = TtsPreferences.speakers_definition
    yield
    TtsPreferences.language = language
    TtsPreferences.auto_speak_definitions = auto_speak
    TtsPreferences.speakers_word_formations = formations
    TtsPreferences.speakers_word = word
    TtsPreferences.speakers_definition = definition


def _speaker_icon_count(card: ft.Container) -> int:
    column = card.content
    assert isinstance(column, ft.Column)
    count = 0
    for row in column.controls:
        assert isinstance(row, ft.Row)
        for control in row.controls:
            if isinstance(control, ft.IconButton):
                count += 1
    return count


def test_tts_preferences_default_to_english_and_auto_speak_on():
    assert TtsPreferences.language == DEFAULT_LANGUAGE
    assert TtsPreferences.auto_speak_definitions is True
    assert TtsPreferences.speakers_word_formations is True
    assert TtsPreferences.speakers_word is True
    assert TtsPreferences.speakers_definition is False
    assert "pl" in LANGUAGE_CODES
    assert "en" in LANGUAGE_CODES


def test_normalize_language_falls_back_to_english():
    assert TtsPreferences.normalize_language("pl") == "pl"
    assert TtsPreferences.normalize_language("nope") == DEFAULT_LANGUAGE
    assert TtsPreferences.normalize_language(None) == DEFAULT_LANGUAGE


def test_parse_auto_speak_defaults_on(restore_tts_preferences):
    assert TtsPreferences.parse_auto_speak(None) is True
    assert TtsPreferences.parse_auto_speak("true") is True
    assert TtsPreferences.parse_auto_speak("false") is False
    assert TtsPreferences.parse_auto_speak("0") is False


def test_parse_speaker_switches_use_documented_defaults(restore_tts_preferences):
    assert TtsPreferences.parse_speakers_word_formations(None) is True
    assert TtsPreferences.parse_speakers_word_formations("false") is False
    assert TtsPreferences.parse_speakers_word(None) is True
    assert TtsPreferences.parse_speakers_word("0") is False
    assert TtsPreferences.parse_speakers_definition(None) is False
    assert TtsPreferences.parse_speakers_definition("true") is True
    assert TtsPreferences.parse_speakers_definition("false") is False


def test_settings_includes_tts_section(restore_tts_preferences):
    from learning_app.ui.screens.settings_control import DashedDivider, SettingsControl

    TtsPreferences.language = "en"
    TtsPreferences.auto_speak_definitions = True
    TtsPreferences.speakers_word_formations = True
    TtsPreferences.speakers_word = True
    TtsPreferences.speakers_definition = False
    screen = SettingsControl(SimpleNamespace())

    assert screen.tts_heading.value == "Text to speech"
    assert screen.tts_language_dropdown.value == TtsPreferences.language
    option_keys = {option.key for option in screen.tts_language_dropdown.options}
    assert option_keys == set(LANGUAGE_CODES)
    assert "pl" in option_keys
    assert screen.tts_auto_speak_switch.value is True
    assert screen.tts_speakers_word_formations_switch.value is True
    assert screen.tts_speakers_word_switch.value is True
    assert screen.tts_speakers_definition_switch.value is False
    assert screen.tts_speakers_heading.value == "Word list speakers"
    assert "set word list cards" in screen.tts_speakers_description.value
    assert screen.tts_speakers_formations_group.controls == [
        screen.tts_speakers_formations_heading,
        screen.tts_speakers_formations_description,
        screen.tts_speakers_word_formations_row,
        screen.tts_speakers_formations_preview,
    ]
    assert screen.tts_speakers_definitions_group.controls == [
        screen.tts_speakers_definitions_heading,
        screen.tts_speakers_definitions_description,
        screen.tts_speakers_word_row,
        screen.tts_speakers_definition_row,
        screen.tts_speakers_definition_hint,
        screen.tts_speakers_definitions_preview,
    ]
    assert "different language" in screen.tts_speakers_definition_hint.value
    assert "globally" in screen.tts_speakers_definition_hint.value
    assert screen.tts_speakers_group.controls == [
        screen.tts_speakers_heading,
        screen.tts_speakers_description,
        screen.tts_speakers_formations_group,
        screen.tts_speakers_definitions_group,
    ]
    formation_values = [
        row.controls[1].value
        for row in screen.tts_speakers_formations_preview.content.controls
    ]
    assert formation_values == ["assist", "assistant", "assistance"]
    definition_labels = [
        row.controls[0].value
        for row in screen.tts_speakers_definitions_preview.content.controls
    ]
    assert definition_labels == ["Definition ", "Word        "]
    assert _speaker_icon_count(screen.tts_speakers_formations_preview) == 3
    assert _speaker_icon_count(screen.tts_speakers_definitions_preview) == 1
    assert screen.tts_section.controls == [
        screen.tts_heading,
        screen.tts_language_dropdown,
        screen.tts_auto_speak_row,
        screen.tts_speakers_divider,
        screen.tts_speakers_group,
    ]
    assert isinstance(screen.tts_speakers_divider, DashedDivider)
    assert isinstance(screen.tts_speakers_divider.content, ft.Row)
    assert len(screen.tts_speakers_divider.content.controls) > 1
    assert screen.tts_speakers_divider.content.spacing == DashedDivider._GAP
    assert screen.controls == [
        screen.controls[0],
        screen.appearance_section,
        screen.tts_section_divider,
        screen.tts_section,
        screen.learning_section_divider,
        screen.learning_section,
        screen.demo_section_divider,
        screen.demo_section,
        screen.controls[-1],
    ]
    assert screen.controls[-1].height == 32
    for divider in (
        screen.tts_section_divider,
        screen.learning_section_divider,
        screen.demo_section_divider,
    ):
        assert isinstance(divider.content, ft.Divider)
        assert divider.content.thickness == 1
        assert divider.content.color == ft.Colors.OUTLINE_VARIANT


def test_settings_speaker_switches_update_runtime_flags(restore_tts_preferences):
    from learning_app.ui.screens.settings_control import SettingsControl

    TtsPreferences.speakers_word_formations = True
    TtsPreferences.speakers_word = True
    TtsPreferences.speakers_definition = False
    page = SimpleNamespace(run_task=lambda *args, **kwargs: None)
    screen = SettingsControl(page)

    screen.tts_speakers_word_formations_switch.value = False
    screen.on_tts_speakers_word_formations_change(
        SimpleNamespace(control=screen.tts_speakers_word_formations_switch)
    )
    screen.tts_speakers_word_switch.value = False
    screen.on_tts_speakers_word_change(
        SimpleNamespace(control=screen.tts_speakers_word_switch)
    )
    screen.tts_speakers_definition_switch.value = True
    screen.on_tts_speakers_definition_change(
        SimpleNamespace(control=screen.tts_speakers_definition_switch)
    )

    assert TtsPreferences.speakers_word_formations is False
    assert TtsPreferences.speakers_word is False
    assert TtsPreferences.speakers_definition is True
    assert _speaker_icon_count(screen.tts_speakers_formations_preview) == 0
    assert _speaker_icon_count(screen.tts_speakers_definitions_preview) == 1
