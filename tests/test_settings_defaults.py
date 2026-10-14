"""Tests for the Settings restore-defaults control."""

from types import SimpleNamespace

import flet as ft
import pytest

from learning_app.ui.app_theme import AppTheme
from learning_app.ui.learn_preferences import (
    DEFINITIONS_QUEUE_SIZE_KEY,
    RETRY_UNTIL_CORRECT_KEY,
    WORD_FORMATIONS_QUEUE_SIZE_KEY,
    LearnPreferences,
)
from learning_app.ui.tts_preferences import (
    AUTO_SPEAK_DEFINITIONS_KEY,
    DEFAULT_LANGUAGE,
    LANGUAGE_KEY,
    SPEAKERS_DEFINITION_KEY,
    SPEAKERS_WORD_FORMATIONS_KEY,
    SPEAKERS_WORD_KEY,
    TtsPreferences,
)


class MemoryPreferences:
    def __init__(self):
        self.data = {}

    async def set(self, key, value):
        self.data[key] = value
        return True

    async def get(self, key):
        return self.data.get(key)

    async def contains_key(self, key):
        return key in self.data

    async def remove(self, key):
        existed = key in self.data
        self.data.pop(key, None)
        return existed


@pytest.fixture
def restore_settings_preferences():
    theme_mode = AppTheme.theme_mode
    dark_slider = AppTheme.dark_theme_slider_value
    light_slider = AppTheme.light_theme_slider_value
    dark_bg = AppTheme.dark_theme_bgcolor
    light_bg = AppTheme.light_theme_bgcolor
    language = TtsPreferences.language
    auto_speak = TtsPreferences.auto_speak_definitions
    formations = TtsPreferences.speakers_word_formations
    word = TtsPreferences.speakers_word
    definition = TtsPreferences.speakers_definition
    retry = LearnPreferences.retry_until_correct
    words_queue = LearnPreferences.word_formations_queue_size
    definitions_queue = LearnPreferences.definitions_queue_size
    yield
    AppTheme.theme_mode = theme_mode
    AppTheme.dark_theme_slider_value = dark_slider
    AppTheme.light_theme_slider_value = light_slider
    AppTheme.dark_theme_bgcolor = dark_bg
    AppTheme.light_theme_bgcolor = light_bg
    TtsPreferences.language = language
    TtsPreferences.auto_speak_definitions = auto_speak
    TtsPreferences.speakers_word_formations = formations
    TtsPreferences.speakers_word = word
    TtsPreferences.speakers_definition = definition
    LearnPreferences.retry_until_correct = retry
    LearnPreferences.word_formations_queue_size = words_queue
    LearnPreferences.definitions_queue_size = definitions_queue


def _patch_storage(monkeypatch) -> MemoryPreferences:
    storage = MemoryPreferences()

    def get_storage():
        return storage

    for target in (
        "learning_app.ui.screens.settings_control.get_shared_preferences",
        "learning_app.ui.learn_preferences.get_shared_preferences",
        "learning_app.ui.tts_preferences.get_shared_preferences",
        "learning_app.ui.app_theme.get_shared_preferences",
    ):
        monkeypatch.setattr(target, get_storage)
    return storage


def _default_color() -> str:
    return AppTheme._normalize_color(AppTheme.DEFAULT_BGCOLOR)


def _apply_saved_defaults() -> None:
    color = _default_color()
    AppTheme.theme_mode = AppTheme.DEFAULT_THEME_MODE
    AppTheme.dark_theme_slider_value = AppTheme.DEFAULT_SLIDER_VALUE
    AppTheme.light_theme_slider_value = AppTheme.DEFAULT_SLIDER_VALUE
    AppTheme.dark_theme_bgcolor = color
    AppTheme.light_theme_bgcolor = color
    TtsPreferences.language = DEFAULT_LANGUAGE
    TtsPreferences.auto_speak_definitions = TtsPreferences.DEFAULT_AUTO_SPEAK_DEFINITIONS
    TtsPreferences.speakers_word_formations = (
        TtsPreferences.DEFAULT_SPEAKERS_WORD_FORMATIONS
    )
    TtsPreferences.speakers_word = TtsPreferences.DEFAULT_SPEAKERS_WORD
    TtsPreferences.speakers_definition = TtsPreferences.DEFAULT_SPEAKERS_DEFINITION
    LearnPreferences.retry_until_correct = LearnPreferences.RETRY_UNTIL_CORRECT_DEFAULT
    LearnPreferences.word_formations_queue_size = (
        LearnPreferences.WORD_FORMATIONS_QUEUE_DEFAULT
    )
    LearnPreferences.definitions_queue_size = LearnPreferences.DEFINITIONS_QUEUE_DEFAULT


def _apply_custom_settings() -> None:
    AppTheme.theme_mode = ft.ThemeMode.LIGHT
    AppTheme.light_theme_slider_value = 4
    AppTheme.dark_theme_slider_value = 1
    AppTheme.light_theme_bgcolor = "white"
    AppTheme.dark_theme_bgcolor = "#000000"
    TtsPreferences.language = "pl"
    TtsPreferences.auto_speak_definitions = False
    TtsPreferences.speakers_word_formations = False
    TtsPreferences.speakers_word = False
    TtsPreferences.speakers_definition = True
    LearnPreferences.retry_until_correct = False
    LearnPreferences.word_formations_queue_size = 8
    LearnPreferences.definitions_queue_size = 14


def _page(theme_mode):
    dialogs = []
    view = SimpleNamespace(bgcolor=None)
    page = SimpleNamespace(
        theme_mode=theme_mode,
        bgcolor=None,
        views=[view],
        dialogs=dialogs,
        update=lambda: None,
    )
    page.show_dialog = dialogs.append
    return page, view


def _snack_text(snack) -> str:
    content = snack.content
    if isinstance(content, str):
        return content
    return content.value


def _speaker_icon_count(card: ft.Container) -> int:
    column = card.content
    count = 0
    for row in column.controls:
        for control in row.controls:
            if isinstance(control, ft.IconButton):
                count += 1
    return count


def test_defaults_section_is_first_content_above_appearance(restore_settings_preferences):
    from learning_app.ui.layout_metrics import LayoutMetrics
    from learning_app.ui.screens.settings_control import SettingsControl

    screen = SettingsControl(SimpleNamespace())

    assert screen.defaults_heading.value == "Defaults"
    assert screen.defaults_heading.size == 18
    assert screen.defaults_heading.weight == ft.FontWeight.BOLD
    assert screen.defaults_description.value == (
        "Restore every setting on this page to its original value. "
        "Learning sets are not changed."
    )
    assert screen.defaults_description.size == 14
    assert screen.restore_defaults_button.content == "Restore defaults"
    assert screen.defaults_section.controls == [
        screen.defaults_heading,
        screen.defaults_description,
        screen.restore_defaults_button,
    ]
    assert screen.controls[0].height == 24
    assert screen.controls[1] is screen.defaults_section
    assert screen.controls[2] is screen.defaults_section_divider
    content_sections = [
        screen.defaults_section,
        screen.appearance_section,
        screen.tts_section,
        screen.learning_section,
        screen.demo_section,
    ]
    indexes = [screen.controls.index(section) for section in content_sections]
    assert indexes == sorted(indexes)
    assert indexes[0] < screen.controls.index(screen.appearance_section)

    screen.apply_layout(
        LayoutMetrics(
            viewport_width=800,
            viewport_height=600,
            body_width=400,
            form_width=400,
            settings_width=420,
            content_height=500,
            breakpoint="normal",
        )
    )
    assert screen.defaults_heading.width == 420
    assert screen.defaults_description.width == 420
    assert screen.restore_defaults_button.width == 420
    assert screen.defaults_section.width == 420
    assert screen.defaults_section_divider.width == 420


async def test_restore_defaults_resets_preferences_and_undo_restores_snapshot(
    restore_settings_preferences, monkeypatch
):
    from learning_app.ui.screens.settings_control import SettingsControl

    demo_calls = []
    monkeypatch.setattr(
        "learning_app.ui.screens.settings_control.install_demo_sets",
        lambda: demo_calls.append("demo"),
    )
    storage = _patch_storage(monkeypatch)
    _apply_custom_settings()
    page, view = _page(ft.ThemeMode.LIGHT)
    screen = SettingsControl(page)

    await screen.on_restore_defaults_click(SimpleNamespace())

    color = _default_color()
    assert AppTheme.theme_mode == AppTheme.DEFAULT_THEME_MODE
    assert AppTheme.dark_theme_slider_value == AppTheme.DEFAULT_SLIDER_VALUE
    assert AppTheme.light_theme_slider_value == AppTheme.DEFAULT_SLIDER_VALUE
    assert AppTheme.dark_theme_bgcolor == color
    assert AppTheme.light_theme_bgcolor == color
    assert TtsPreferences.language == DEFAULT_LANGUAGE
    assert TtsPreferences.auto_speak_definitions is True
    assert TtsPreferences.speakers_word_formations is True
    assert TtsPreferences.speakers_word is True
    assert TtsPreferences.speakers_definition is False
    assert LearnPreferences.retry_until_correct is True
    assert (
        LearnPreferences.word_formations_queue_size
        == LearnPreferences.WORD_FORMATIONS_QUEUE_DEFAULT
    )
    assert (
        LearnPreferences.definitions_queue_size
        == LearnPreferences.DEFINITIONS_QUEUE_DEFAULT
    )
    assert screen.theme_switch.value is False
    assert screen.background_shade_slider.slider.value == AppTheme.DEFAULT_SLIDER_VALUE
    assert screen.tts_language_dropdown.value == DEFAULT_LANGUAGE
    assert screen.tts_auto_speak_switch.value is True
    assert screen.tts_speakers_word_formations_switch.value is True
    assert screen.tts_speakers_word_switch.value is True
    assert screen.tts_speakers_definition_switch.value is False
    assert screen.retry_until_correct_switch.value is True
    assert screen.word_formations_queue_slider.slider.value == 5
    assert screen.word_formations_queue_slider.label.value == "Word formations: 5"
    assert screen.definitions_queue_slider.slider.value == 10
    assert screen.definitions_queue_slider.label.value == "Definitions: 10"
    assert _speaker_icon_count(screen.tts_speakers_formations_preview) == 3
    assert _speaker_icon_count(screen.tts_speakers_definitions_preview) == 1
    assert page.theme_mode == ft.ThemeMode.DARK
    assert page.bgcolor == color
    assert view.bgcolor == color
    assert demo_calls == []
    assert storage.data == {
        "theme_mode": "dark",
        "dark_theme_slider_value": "2",
        "light_theme_slider_value": "2",
        "dark_theme_bgcolor": color,
        "light_theme_bgcolor": color,
        LANGUAGE_KEY: DEFAULT_LANGUAGE,
        AUTO_SPEAK_DEFINITIONS_KEY: "true",
        SPEAKERS_WORD_FORMATIONS_KEY: "true",
        SPEAKERS_WORD_KEY: "true",
        SPEAKERS_DEFINITION_KEY: "false",
        RETRY_UNTIL_CORRECT_KEY: "true",
        WORD_FORMATIONS_QUEUE_SIZE_KEY: "5",
        DEFINITIONS_QUEUE_SIZE_KEY: "10",
    }

    assert len(page.dialogs) == 1
    snack = page.dialogs[0]
    assert isinstance(snack, ft.SnackBar)
    assert _snack_text(snack) == "Settings restored to their defaults."
    assert snack.action == "Undo"
    assert snack.on_action is not None
    assert snack.persist is False
    assert snack.duration.milliseconds == 4000

    LearnPreferences.word_formations_queue_size = 9
    screen.word_formations_queue_slider.slider.value = 9
    screen.word_formations_queue_slider.label.value = "Word formations: 9"

    await snack.on_action(None)

    assert AppTheme.theme_mode == ft.ThemeMode.LIGHT
    assert AppTheme.dark_theme_slider_value == 1
    assert AppTheme.light_theme_slider_value == 4
    assert AppTheme.dark_theme_bgcolor == "#000000"
    assert AppTheme.light_theme_bgcolor == "white"
    assert TtsPreferences.language == "pl"
    assert TtsPreferences.auto_speak_definitions is False
    assert TtsPreferences.speakers_word_formations is False
    assert TtsPreferences.speakers_word is False
    assert TtsPreferences.speakers_definition is True
    assert LearnPreferences.retry_until_correct is False
    assert LearnPreferences.word_formations_queue_size == 8
    assert LearnPreferences.definitions_queue_size == 14
    assert screen.theme_switch.value is True
    assert screen.background_shade_slider.slider.value == 4
    assert screen.tts_language_dropdown.value == "pl"
    assert screen.tts_auto_speak_switch.value is False
    assert screen.tts_speakers_word_formations_switch.value is False
    assert screen.tts_speakers_word_switch.value is False
    assert screen.tts_speakers_definition_switch.value is True
    assert screen.retry_until_correct_switch.value is False
    assert screen.word_formations_queue_slider.slider.value == 8
    assert screen.word_formations_queue_slider.label.value == "Word formations: 8"
    assert screen.definitions_queue_slider.slider.value == 14
    assert screen.definitions_queue_slider.label.value == "Definitions: 14"
    assert _speaker_icon_count(screen.tts_speakers_formations_preview) == 0
    assert _speaker_icon_count(screen.tts_speakers_definitions_preview) == 1
    assert page.theme_mode == ft.ThemeMode.LIGHT
    assert page.bgcolor == "white"
    assert view.bgcolor == "white"
    assert storage.data == {
        "theme_mode": "light",
        "dark_theme_slider_value": "1",
        "light_theme_slider_value": "4",
        "dark_theme_bgcolor": "#000000",
        "light_theme_bgcolor": "white",
        LANGUAGE_KEY: "pl",
        AUTO_SPEAK_DEFINITIONS_KEY: "false",
        SPEAKERS_WORD_FORMATIONS_KEY: "false",
        SPEAKERS_WORD_KEY: "false",
        SPEAKERS_DEFINITION_KEY: "true",
        RETRY_UNTIL_CORRECT_KEY: "false",
        WORD_FORMATIONS_QUEUE_SIZE_KEY: "8",
        DEFINITIONS_QUEUE_SIZE_KEY: "14",
    }
    assert demo_calls == []


async def test_restore_defaults_when_already_default_has_no_undo(
    restore_settings_preferences, monkeypatch
):
    from learning_app.ui.screens.settings_control import SettingsControl

    storage = _patch_storage(monkeypatch)
    storage.data["untouched"] = "keep"
    _apply_saved_defaults()
    page, view = _page(ft.ThemeMode.DARK)
    page.bgcolor = "leave-me"
    view.bgcolor = "leave-me"
    screen = SettingsControl(page)
    before = {
        "theme_mode": AppTheme.theme_mode,
        "dark_slider": AppTheme.dark_theme_slider_value,
        "light_slider": AppTheme.light_theme_slider_value,
        "dark_bg": AppTheme.dark_theme_bgcolor,
        "light_bg": AppTheme.light_theme_bgcolor,
        "language": TtsPreferences.language,
        "auto_speak": TtsPreferences.auto_speak_definitions,
        "formations": TtsPreferences.speakers_word_formations,
        "word": TtsPreferences.speakers_word,
        "definition": TtsPreferences.speakers_definition,
        "retry": LearnPreferences.retry_until_correct,
        "words_queue": LearnPreferences.word_formations_queue_size,
        "definitions_queue": LearnPreferences.definitions_queue_size,
        "switch": screen.theme_switch.value,
        "shade": screen.background_shade_slider.slider.value,
        "dropdown": screen.tts_language_dropdown.value,
    }

    await screen.on_restore_defaults_click(SimpleNamespace())

    assert AppTheme.theme_mode == before["theme_mode"]
    assert AppTheme.dark_theme_slider_value == before["dark_slider"]
    assert AppTheme.light_theme_slider_value == before["light_slider"]
    assert AppTheme.dark_theme_bgcolor == before["dark_bg"]
    assert AppTheme.light_theme_bgcolor == before["light_bg"]
    assert TtsPreferences.language == before["language"]
    assert TtsPreferences.auto_speak_definitions == before["auto_speak"]
    assert TtsPreferences.speakers_word_formations == before["formations"]
    assert TtsPreferences.speakers_word == before["word"]
    assert TtsPreferences.speakers_definition == before["definition"]
    assert LearnPreferences.retry_until_correct == before["retry"]
    assert LearnPreferences.word_formations_queue_size == before["words_queue"]
    assert LearnPreferences.definitions_queue_size == before["definitions_queue"]
    assert screen.theme_switch.value == before["switch"]
    assert screen.background_shade_slider.slider.value == before["shade"]
    assert screen.tts_language_dropdown.value == before["dropdown"]
    assert page.theme_mode == ft.ThemeMode.DARK
    assert page.bgcolor == "leave-me"
    assert view.bgcolor == "leave-me"
    assert storage.data == {"untouched": "keep"}
    assert len(page.dialogs) == 1
    snack = page.dialogs[0]
    assert isinstance(snack, ft.SnackBar)
    assert _snack_text(snack) == "Settings are already at their defaults."
    assert snack.action is None
    assert snack.on_action is None
    assert snack.persist is None
