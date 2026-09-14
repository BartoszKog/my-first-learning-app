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
    yield
    TtsPreferences.language = language
    TtsPreferences.auto_speak_definitions = auto_speak


def test_tts_preferences_default_to_english_and_auto_speak_on():
    assert TtsPreferences.language == DEFAULT_LANGUAGE
    assert TtsPreferences.auto_speak_definitions is True
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


def test_settings_includes_tts_section(restore_tts_preferences):
    from learning_app.ui.screens.settings_control import SettingsControl

    TtsPreferences.language = "en"
    TtsPreferences.auto_speak_definitions = True
    screen = SettingsControl(SimpleNamespace())

    assert screen.tts_heading.value == "Text to speech"
    assert screen.tts_language_dropdown.value == TtsPreferences.language
    option_keys = {option.key for option in screen.tts_language_dropdown.options}
    assert option_keys == set(LANGUAGE_CODES)
    assert "pl" in option_keys
    assert screen.tts_auto_speak_switch.value is True
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
