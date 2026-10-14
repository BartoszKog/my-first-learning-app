from dataclasses import dataclass

import flet as ft

from learning_app.data.demo_sets import install_demo_sets
from learning_app.ui.body_registry import BodyRegistry
from learning_app.ui.layout_host import control_is_on_page
from learning_app.ui.layout_metrics import LayoutMetrics
from learning_app.ui.app_theme import AppTheme
from learning_app.ui.page_functions import create_alert_dialog
from learning_app.ui.preferences import get_shared_preferences
from learning_app.ui.learn_preferences import LearnPreferences
from learning_app.ui.routable_screen import RoutableScreenMixin
from learning_app.ui.tts_preferences import DEFAULT_LANGUAGE, TTS_LANGUAGES, TtsPreferences

_PREVIEW_LABEL_COLOR = ft.Colors.BLUE_GREY_500
# Same outline as word-list "To learn" cards — visible on dark backgrounds.
_FORM_BORDER_COLOR = ft.Colors.BLUE_GREY_700
_PREVIEW_BORDER = ft.Border.all(1.5, _FORM_BORDER_COLOR)


def _preview_speaker_button() -> ft.IconButton:
    return ft.IconButton(
        icon=ft.Icons.VOLUME_UP,
        icon_color=_PREVIEW_LABEL_COLOR,
        icon_size=16,
        padding=0,
        height=18,
        visual_density=ft.VisualDensity.COMPACT,
        size_constraints=ft.BoxConstraints(
            min_width=18,
            min_height=18,
            max_width=18,
            max_height=18,
        ),
        tooltip="Pronounce",
    )


def _preview_field_row(label: str, value: str, *, show_speaker: bool) -> ft.Row:
    controls: list[ft.Control] = [
        ft.Text(label, color=_PREVIEW_LABEL_COLOR),
        ft.Text(value, expand=True),
    ]
    if show_speaker:
        controls.append(_preview_speaker_button())
    return ft.Row(
        controls,
        spacing=4,
        vertical_alignment=ft.CrossAxisAlignment.CENTER,
    )


class SpeakerPreviewCard(ft.Container):
    """Always-visible sample word-list card for Settings speaker switches."""

    def __init__(self, width: float):
        super().__init__()
        self.width = width
        self.padding = 10
        self.border_radius = 5
        self.border = _PREVIEW_BORDER
        self.content = ft.Column(spacing=4)

    def apply_layout(self, width: float):
        self.width = width

    def set_rows(self, rows: list[ft.Row]):
        self.content = ft.Column(rows, spacing=4)


def _formations_preview_rows(*, show_speaker: bool) -> list[ft.Row]:
    return [
        _preview_field_row("Verb         ", "assist", show_speaker=show_speaker),
        _preview_field_row("Person     ", "assistant", show_speaker=show_speaker),
        _preview_field_row("Thing       ", "assistance", show_speaker=show_speaker),
    ]


def _definitions_preview_rows(
    *, show_word_speaker: bool, show_definition_speaker: bool
) -> list[ft.Row]:
    return [
        _preview_field_row(
            "Definition ",
            "a round fruit",
            show_speaker=show_definition_speaker,
        ),
        _preview_field_row(
            "Word        ", "apple", show_speaker=show_word_speaker
        ),
    ]


class DashedDivider(ft.Container):
    """Horizontal dashed rule separating Word list speakers from TTS above."""

    _DASH_WIDTH = 6.0
    _GAP = 4.0
    _DASH_HEIGHT = 1.0

    def __init__(self, width: float):
        super().__init__()
        self.height = 24
        self.alignment = ft.Alignment.CENTER
        self.apply_layout(width)

    def apply_layout(self, width: float):
        self.width = width
        count = max(1, int(width // (self._DASH_WIDTH + self._GAP)))
        self.content = ft.Row(
            [
                ft.Container(
                    width=self._DASH_WIDTH,
                    height=self._DASH_HEIGHT,
                    bgcolor=ft.Colors.OUTLINE_VARIANT,
                )
                for _ in range(count)
            ],
            spacing=self._GAP,
            tight=True,
        )


class BackgroundShadeSlider(ft.Column):
    """Slider that maps shade index 1–4 to light or dark page backgrounds.

    Updates ``AppTheme`` in memory, applies bgcolor to the page, and persists
    the active mode's slider and color keys.
    """

    DARK_THEME_COLORS = [
        "#000000",   # 1 — AMOLED
        "#0F0F0F",   # 2
        "#171717",   # 3
        "#1F1F1F",   # 4
    ]

    LIGHT_THEME_COLORS = [
        ft.Colors.WHITE,
        ft.Colors.SURFACE,
        ft.Colors.BLUE_GREY_50,
        ft.Colors.BLUE_50,
    ]

    def __init__(self, label: str, initial_value: int, width: float):
        super().__init__()
        self.width = width
        initial_value = int(initial_value)
        max_value = len(self.DARK_THEME_COLORS)
        self.label = ft.Text(label)
        self.slider = ft.Slider(
            min=1,
            max=max_value,
            divisions=max_value - 1,
            value=initial_value,
            on_change=self.on_slider_change,
        )
        self.controls = [self.label, self.slider]

    def apply_layout(self, width: float):
        self.width = width

    def on_slider_change(self, e):
        value = int(e.control.value)
        AppTheme.set_slider_value(AppTheme.theme_mode, value)
        if AppTheme.theme_mode == ft.ThemeMode.DARK:
            color = self.DARK_THEME_COLORS[value - 1]
        else:
            color = self.LIGHT_THEME_COLORS[value - 1]

        AppTheme.set_bgcolor(AppTheme.theme_mode, color)

        AppTheme.apply_to_page(self.page)
        self.page.run_task(
            self._save_slider_settings,
            AppTheme.theme_mode.value,
            value,
            color,
        )

        self.page.update()

    async def _save_slider_settings(self, theme_mode_value, value, color):
        await AppTheme.save_slider_settings(theme_mode_value, value, color)

    def update_slider_position(self):
        self.slider.value = AppTheme.get_slider_value()
        self.slider.update()

    def did_mount(self):
        self.update_slider_position()


class PracticeQueueSlider(ft.Column):
    """Slider that sets one practice-queue size and shows the current integer."""

    def __init__(
        self,
        title: str,
        minimum: int,
        maximum: int,
        divisions: int,
        initial_value: int,
        on_change,
        width: float,
    ):
        super().__init__()
        self._title = title
        self._on_change = on_change
        initial_value = int(initial_value)
        self.label = ft.Text(self._format_label(initial_value))
        self.slider = ft.Slider(
            min=minimum,
            max=maximum,
            divisions=divisions,
            value=initial_value,
            on_change=self.on_slider_change,
        )
        self.controls = [self.label, self.slider]
        self.apply_layout(width)

    def _format_label(self, value: int) -> str:
        return f"{self._title}: {int(value)}"

    def apply_layout(self, width: float):
        self.width = width
        self.label.width = width
        self.slider.width = width

    def on_slider_change(self, e):
        value = int(e.control.value)
        self.label.value = self._format_label(value)
        self._on_change(value)
        if control_is_on_page(self.label):
            self.label.update()


def _stored_color(color) -> str | None:
    """Return a preference color string, or ``None`` when unset."""
    normalized = AppTheme._normalize_color(color)
    if normalized is None:
        return None
    if isinstance(normalized, str):
        return normalized
    return str(normalized)


@dataclass(frozen=True)
class _SettingsSnapshot:
    """Runtime Settings preferences that Restore defaults can write back."""

    theme_mode: ft.ThemeMode | None
    dark_theme_slider_value: int
    light_theme_slider_value: int
    dark_theme_bgcolor: str | None
    light_theme_bgcolor: str | None
    language: str
    auto_speak_definitions: bool
    speakers_word_formations: bool
    speakers_word: bool
    speakers_definition: bool
    retry_until_correct: bool
    word_formations_queue_size: int
    definitions_queue_size: int


def _capture_settings() -> _SettingsSnapshot:
    """Read the Settings preferences currently held in memory."""
    return _SettingsSnapshot(
        theme_mode=AppTheme.theme_mode,
        dark_theme_slider_value=int(AppTheme.dark_theme_slider_value),
        light_theme_slider_value=int(AppTheme.light_theme_slider_value),
        dark_theme_bgcolor=_stored_color(AppTheme.dark_theme_bgcolor),
        light_theme_bgcolor=_stored_color(AppTheme.light_theme_bgcolor),
        language=TtsPreferences.language,
        auto_speak_definitions=bool(TtsPreferences.auto_speak_definitions),
        speakers_word_formations=bool(TtsPreferences.speakers_word_formations),
        speakers_word=bool(TtsPreferences.speakers_word),
        speakers_definition=bool(TtsPreferences.speakers_definition),
        retry_until_correct=bool(LearnPreferences.retry_until_correct),
        word_formations_queue_size=int(LearnPreferences.word_formations_queue_size),
        definitions_queue_size=int(LearnPreferences.definitions_queue_size),
    )


def _default_settings() -> _SettingsSnapshot:
    """Original Settings values from theme, TTS, and learn preferences."""
    default_color = _stored_color(AppTheme.DEFAULT_BGCOLOR)
    return _SettingsSnapshot(
        theme_mode=AppTheme.DEFAULT_THEME_MODE,
        dark_theme_slider_value=AppTheme.DEFAULT_SLIDER_VALUE,
        light_theme_slider_value=AppTheme.DEFAULT_SLIDER_VALUE,
        dark_theme_bgcolor=default_color,
        light_theme_bgcolor=default_color,
        language=DEFAULT_LANGUAGE,
        auto_speak_definitions=TtsPreferences.DEFAULT_AUTO_SPEAK_DEFINITIONS,
        speakers_word_formations=TtsPreferences.DEFAULT_SPEAKERS_WORD_FORMATIONS,
        speakers_word=TtsPreferences.DEFAULT_SPEAKERS_WORD,
        speakers_definition=TtsPreferences.DEFAULT_SPEAKERS_DEFINITION,
        retry_until_correct=LearnPreferences.RETRY_UNTIL_CORRECT_DEFAULT,
        word_formations_queue_size=LearnPreferences.WORD_FORMATIONS_QUEUE_DEFAULT,
        definitions_queue_size=LearnPreferences.DEFINITIONS_QUEUE_DEFAULT,
    )


class SettingsControl(RoutableScreenMixin, ft.Column):
    """Settings shell screen with Defaults, Appearance, TTS, Learning, and Demo sets.

    Owns restore-defaults, the light/dark switch, ``BackgroundShadeSlider``,
    TTS language, auto-speak, word-list speakers, learn-queue retry,
    practice-queue size sliders, and demo-set installation. Persistence
    goes through preferences, ``AppTheme``, ``TtsPreferences``, and
    ``LearnPreferences``; shell chrome colors stay in ``app.py``.
    """

    def __init__(self, page):
        super().__init__()
        self.expand = True
        self.scroll = ft.ScrollMode.AUTO
        self.alignment = ft.MainAxisAlignment.START
        self.horizontal_alignment = ft.CrossAxisAlignment.CENTER
        self.spacing = 0
        self._app_page = page
        self._content_width = 300

        self.theme_switch = ft.Switch(
            label=" Light theme",
            label_text_style=ft.TextStyle(size=16),
            value=AppTheme.theme_mode == ft.ThemeMode.LIGHT,
            on_change=self.on_theme_change,
        )

        initial_value = AppTheme.get_slider_value()

        self.background_shade_slider = BackgroundShadeSlider(
            label="Background Shade",
            initial_value=initial_value,
            width=self._content_width,
        )

        self.theme_switch_row = ft.Row(
            [self.theme_switch],
            alignment=ft.MainAxisAlignment.START,
        )

        self.defaults_heading = ft.Text(
            "Defaults",
            size=18,
            weight=ft.FontWeight.BOLD,
            width=self._content_width,
        )
        self.defaults_description = ft.Text(
            "Restore every setting on this page to its original value. Learning sets are not changed.",
            size=14,
            width=self._content_width,
        )
        self.restore_defaults_button = ft.Button(
            content="Restore defaults",
            on_click=self.on_restore_defaults_click,
            width=self._content_width,
        )
        self.appearance_heading = ft.Text(
            "Appearance",
            size=18,
            weight=ft.FontWeight.BOLD,
            width=self._content_width,
        )
        self.demo_heading = ft.Text(
            "Demo sets",
            size=18,
            weight=ft.FontWeight.BOLD,
            width=self._content_width,
        )
        self.tts_heading = ft.Text(
            "Text to speech",
            size=18,
            weight=ft.FontWeight.BOLD,
            width=self._content_width,
        )
        self.tts_language_dropdown = ft.Dropdown(
            label="Language",
            value=TtsPreferences.language,
            options=[
                ft.DropdownOption(key=code, text=label) for code, label in TTS_LANGUAGES
            ],
            width=self._content_width,
            border_color=_FORM_BORDER_COLOR,
            on_select=self.on_tts_language_select,
        )
        self.tts_auto_speak_switch = ft.Switch(
            label=" Pronounce after Check",
            label_text_style=ft.TextStyle(size=16),
            value=TtsPreferences.auto_speak_definitions,
            on_change=self.on_tts_auto_speak_change,
        )
        self.tts_auto_speak_row = ft.Row(
            [self.tts_auto_speak_switch],
            alignment=ft.MainAxisAlignment.START,
        )
        self.tts_speakers_heading = ft.Text(
            "Word list speakers",
            size=16,
            weight=ft.FontWeight.BOLD,
            width=self._content_width,
        )
        self.tts_speakers_description = ft.Text(
            "Show or hide speaker buttons on the set word list cards.",
            size=14,
            width=self._content_width,
        )
        self.tts_speakers_formations_heading = ft.Text(
            "Word formations",
            size=14,
            weight=ft.FontWeight.W_600,
            width=self._content_width,
        )
        self.tts_speakers_formations_description = ft.Text(
            "Covers verb, person, thing, adjective, and adverb fields.",
            size=13,
            width=self._content_width,
        )
        self.tts_speakers_word_formations_switch = ft.Switch(
            label=" Word formation speakers",
            label_text_style=ft.TextStyle(size=16),
            value=TtsPreferences.speakers_word_formations,
            on_change=self.on_tts_speakers_word_formations_change,
        )
        self.tts_speakers_word_formations_row = ft.Row(
            [self.tts_speakers_word_formations_switch],
            alignment=ft.MainAxisAlignment.START,
        )
        self.tts_speakers_formations_preview = SpeakerPreviewCard(
            self._content_width
        )
        self.tts_speakers_formations_group = ft.Column(
            controls=[
                self.tts_speakers_formations_heading,
                self.tts_speakers_formations_description,
                self.tts_speakers_word_formations_row,
                self.tts_speakers_formations_preview,
            ],
            spacing=6,
            width=self._content_width,
        )
        self.tts_speakers_definitions_heading = ft.Text(
            "Definitions",
            size=14,
            weight=ft.FontWeight.W_600,
            width=self._content_width,
        )
        self.tts_speakers_definitions_description = ft.Text(
            "Word and Definition are the two fields on definition cards.",
            size=13,
            width=self._content_width,
        )
        self.tts_speakers_word_switch = ft.Switch(
            label=" Word speakers",
            label_text_style=ft.TextStyle(size=16),
            value=TtsPreferences.speakers_word,
            on_change=self.on_tts_speakers_word_change,
        )
        self.tts_speakers_word_row = ft.Row(
            [self.tts_speakers_word_switch],
            alignment=ft.MainAxisAlignment.START,
        )
        self.tts_speakers_definition_switch = ft.Switch(
            label=" Definition speakers",
            label_text_style=ft.TextStyle(size=16),
            value=TtsPreferences.speakers_definition,
            on_change=self.on_tts_speakers_definition_change,
        )
        self.tts_speakers_definition_row = ft.Row(
            [self.tts_speakers_definition_switch],
            alignment=ft.MainAxisAlignment.START,
        )
        self.tts_speakers_definition_hint = ft.Text(
            "Definitions may be written in a different language than the one "
            "you are learning. TTS language is set globally above, so "
            "pronouncing definitions can sound wrong when that language does "
            "not match the definition text.",
            size=13,
            width=self._content_width,
        )
        self.tts_speakers_definitions_preview = SpeakerPreviewCard(
            self._content_width
        )
        self.tts_speakers_definitions_group = ft.Column(
            controls=[
                self.tts_speakers_definitions_heading,
                self.tts_speakers_definitions_description,
                self.tts_speakers_word_row,
                self.tts_speakers_definition_row,
                self.tts_speakers_definition_hint,
                self.tts_speakers_definitions_preview,
            ],
            spacing=6,
            width=self._content_width,
        )
        self._refresh_speakers_preview()
        self.tts_speakers_divider = DashedDivider(self._content_width)
        self.tts_speakers_group = ft.Column(
            controls=[
                self.tts_speakers_heading,
                self.tts_speakers_description,
                self.tts_speakers_formations_group,
                self.tts_speakers_definitions_group,
            ],
            spacing=12,
            width=self._content_width,
        )
        self.learning_heading = ft.Text(
            "Learning",
            size=18,
            weight=ft.FontWeight.BOLD,
            width=self._content_width,
        )
        self.retry_until_correct_switch = ft.Switch(
            label=" Retype until correct",
            label_text_style=ft.TextStyle(size=16),
            value=LearnPreferences.retry_until_correct,
            on_change=self.on_retry_until_correct_change,
        )
        self.retry_until_correct_row = ft.Row(
            [self.retry_until_correct_switch],
            alignment=ft.MainAxisAlignment.START,
        )
        self.retry_until_correct_description = ft.Text(
            "After a wrong answer, type the correct one before continuing. Extra attempts do not change statistics.",
            size=14,
            width=self._content_width,
        )
        self.queue_size_divider = DashedDivider(self._content_width)
        self.queue_size_heading = ft.Text(
            "Queue size",
            size=16,
            weight=ft.FontWeight.BOLD,
            width=self._content_width,
        )
        self.queue_size_description = ft.Text(
            "How many items are drawn into the next practice round. Set word "
            "formations and definitions separately. The round already started "
            "keeps its length.",
            size=14,
            width=self._content_width,
        )
        self.word_formations_queue_slider = PracticeQueueSlider(
            title="Word formations",
            minimum=LearnPreferences.WORD_FORMATIONS_QUEUE_MIN,
            maximum=LearnPreferences.WORD_FORMATIONS_QUEUE_MAX,
            divisions=7,
            initial_value=LearnPreferences.word_formations_queue_size,
            on_change=self.on_word_formations_queue_size_change,
            width=self._content_width,
        )
        self.definitions_queue_slider = PracticeQueueSlider(
            title="Definitions",
            minimum=LearnPreferences.DEFINITIONS_QUEUE_MIN,
            maximum=LearnPreferences.DEFINITIONS_QUEUE_MAX,
            divisions=11,
            initial_value=LearnPreferences.definitions_queue_size,
            on_change=self.on_definitions_queue_size_change,
            width=self._content_width,
        )
        self.demo_description = ft.Text(
            "Add sample learning sets so you can try the app quickly.",
            size=14,
            width=self._content_width,
        )
        self.add_demo_button = ft.Button(
            content="Add demo sets",
            on_click=self.on_add_demo_sets_click,
            width=self._content_width,
        )

        self.defaults_section = ft.Column(
            controls=[
                self.defaults_heading,
                self.defaults_description,
                self.restore_defaults_button,
            ],
            spacing=12,
            width=self._content_width,
        )
        self.appearance_section = ft.Column(
            controls=[
                self.appearance_heading,
                self.theme_switch_row,
                self.background_shade_slider,
            ],
            spacing=16,
            width=self._content_width,
        )
        self.tts_section = ft.Column(
            controls=[
                self.tts_heading,
                self.tts_language_dropdown,
                self.tts_auto_speak_row,
                self.tts_speakers_divider,
                self.tts_speakers_group,
            ],
            spacing=16,
            width=self._content_width,
        )
        self.learning_section = ft.Column(
            controls=[
                self.learning_heading,
                self.retry_until_correct_row,
                self.retry_until_correct_description,
                self.queue_size_divider,
                self.queue_size_heading,
                self.queue_size_description,
                self.word_formations_queue_slider,
                self.definitions_queue_slider,
            ],
            spacing=16,
            width=self._content_width,
        )
        self.demo_section = ft.Column(
            controls=[
                self.demo_heading,
                self.demo_description,
                self.add_demo_button,
            ],
            spacing=12,
            width=self._content_width,
        )

        self.defaults_section_divider = self._section_divider()
        self.tts_section_divider = self._section_divider()
        self.learning_section_divider = self._section_divider()
        self.demo_section_divider = self._section_divider()

        self.controls = [
            ft.Container(height=24),
            self.defaults_section,
            self.defaults_section_divider,
            self.appearance_section,
            self.tts_section_divider,
            self.tts_section,
            self.learning_section_divider,
            self.learning_section,
            self.demo_section_divider,
            self.demo_section,
            ft.Container(height=32),
        ]

    def _section_divider(self) -> ft.Container:
        return ft.Container(
            content=ft.Divider(
                height=32,
                thickness=1,
                color=ft.Colors.OUTLINE_VARIANT,
            ),
            width=self._content_width,
        )

    def _get_page(self):
        if control_is_on_page(self):
            return self.page
        return self._app_page

    def _refresh_speakers_preview(self):
        self.tts_speakers_formations_preview.set_rows(
            _formations_preview_rows(
                show_speaker=TtsPreferences.speakers_word_formations
            )
        )
        self.tts_speakers_definitions_preview.set_rows(
            _definitions_preview_rows(
                show_word_speaker=TtsPreferences.speakers_word,
                show_definition_speaker=TtsPreferences.speakers_definition,
            )
        )
        if control_is_on_page(self.tts_speakers_formations_preview):
            self.tts_speakers_formations_preview.update()
        if control_is_on_page(self.tts_speakers_definitions_preview):
            self.tts_speakers_definitions_preview.update()

    def apply_layout(self, metrics: LayoutMetrics | None = None):
        metrics = self.resolve_layout_metrics(metrics)

        self._content_width = metrics.settings_width
        for control in (
            self.defaults_heading,
            self.defaults_description,
            self.restore_defaults_button,
            self.defaults_section,
            self.defaults_section_divider,
            self.appearance_heading,
            self.demo_heading,
            self.tts_heading,
            self.learning_heading,
            self.demo_description,
            self.retry_until_correct_description,
            self.queue_size_heading,
            self.queue_size_description,
            self.tts_speakers_heading,
            self.tts_speakers_description,
            self.tts_speakers_formations_heading,
            self.tts_speakers_formations_description,
            self.tts_speakers_definitions_heading,
            self.tts_speakers_definitions_description,
            self.tts_speakers_definition_hint,
            self.add_demo_button,
            self.appearance_section,
            self.tts_section,
            self.learning_section,
            self.demo_section,
            self.theme_switch_row,
            self.tts_auto_speak_row,
            self.tts_speakers_group,
            self.tts_speakers_formations_group,
            self.tts_speakers_definitions_group,
            self.tts_speakers_word_formations_row,
            self.tts_speakers_word_row,
            self.tts_speakers_definition_row,
            self.retry_until_correct_row,
            self.tts_language_dropdown,
            self.tts_section_divider,
            self.learning_section_divider,
            self.demo_section_divider,
        ):
            control.width = metrics.settings_width
        self.background_shade_slider.apply_layout(metrics.settings_width)
        self.word_formations_queue_slider.apply_layout(metrics.settings_width)
        self.definitions_queue_slider.apply_layout(metrics.settings_width)
        self.tts_speakers_formations_preview.apply_layout(metrics.settings_width)
        self.tts_speakers_definitions_preview.apply_layout(metrics.settings_width)
        self.tts_speakers_divider.apply_layout(metrics.settings_width)
        self.queue_size_divider.apply_layout(metrics.settings_width)

        self.update_if_mounted()

    def on_theme_change(self, e):
        page = self._get_page()
        if e.control.value:
            page.theme_mode = ft.ThemeMode.LIGHT
            theme_mode_value = ft.ThemeMode.LIGHT.value
        else:
            page.theme_mode = ft.ThemeMode.DARK
            theme_mode_value = ft.ThemeMode.DARK.value

        page.run_task(self._save_theme_mode, theme_mode_value)
        AppTheme.sync_from_page(page)
        AppTheme.apply_to_page(page)
        page.update()
        self.background_shade_slider.update_slider_position()

    async def _save_theme_mode(self, theme_mode_value):
        await get_shared_preferences().set("theme_mode", theme_mode_value)

    def on_tts_language_select(self, e):
        language = TtsPreferences.normalize_language(e.control.value)
        TtsPreferences.language = language
        e.control.value = language
        page = self._get_page()
        if page is not None:
            page.run_task(TtsPreferences.save_language, language)

    def on_tts_auto_speak_change(self, e):
        enabled = bool(e.control.value)
        TtsPreferences.auto_speak_definitions = enabled
        page = self._get_page()
        if page is not None:
            page.run_task(TtsPreferences.save_auto_speak_definitions, enabled)

    def on_tts_speakers_word_formations_change(self, e):
        enabled = bool(e.control.value)
        TtsPreferences.speakers_word_formations = enabled
        page = self._get_page()
        if page is not None:
            page.run_task(TtsPreferences.save_speakers_word_formations, enabled)
        self._refresh_speakers_preview()

    def on_tts_speakers_word_change(self, e):
        enabled = bool(e.control.value)
        TtsPreferences.speakers_word = enabled
        page = self._get_page()
        if page is not None:
            page.run_task(TtsPreferences.save_speakers_word, enabled)
        self._refresh_speakers_preview()

    def on_tts_speakers_definition_change(self, e):
        enabled = bool(e.control.value)
        TtsPreferences.speakers_definition = enabled
        page = self._get_page()
        if page is not None:
            page.run_task(TtsPreferences.save_speakers_definition, enabled)
        self._refresh_speakers_preview()

    def on_retry_until_correct_change(self, e):
        enabled = bool(e.control.value)
        LearnPreferences.retry_until_correct = enabled
        page = self._get_page()
        if page is not None:
            page.run_task(LearnPreferences.save_retry_until_correct, enabled)

    def on_word_formations_queue_size_change(self, size: int):
        size = int(size)
        LearnPreferences.word_formations_queue_size = size
        page = self._get_page()
        if page is not None:
            page.run_task(LearnPreferences.save_word_formations_queue_size, size)

    def on_definitions_queue_size_change(self, size: int):
        size = int(size)
        LearnPreferences.definitions_queue_size = size
        page = self._get_page()
        if page is not None:
            page.run_task(LearnPreferences.save_definitions_queue_size, size)

    async def on_restore_defaults_click(self, e):
        """Reset Settings preferences, or say they are already at defaults.

        A reset snapshots the current values first. The snackbar Undo action
        writes that snapshot back even if the user edits Settings while the
        snackbar is still open. Learning sets, demo data, and CSV progress
        are left alone.
        """
        current = _capture_settings()
        page = self._get_page()
        if current == _default_settings():
            page.show_dialog(
                ft.SnackBar(ft.Text("Settings are already at their defaults."))
            )
            return

        await self._apply_settings_snapshot(_default_settings())

        async def undo(_event=None):
            await self._apply_settings_snapshot(current)

        page.show_dialog(
            ft.SnackBar(
                content=ft.Text("Settings restored to their defaults."),
                action="Undo",
                on_action=undo,
                persist=False,
            )
        )

    async def _apply_settings_snapshot(self, snapshot: _SettingsSnapshot) -> None:
        """Write one snapshot to runtime objects, preferences, and controls."""
        AppTheme.theme_mode = snapshot.theme_mode
        AppTheme.set_slider_value(ft.ThemeMode.DARK, snapshot.dark_theme_slider_value)
        AppTheme.set_slider_value(
            ft.ThemeMode.LIGHT, snapshot.light_theme_slider_value
        )
        AppTheme.set_bgcolor(ft.ThemeMode.DARK, snapshot.dark_theme_bgcolor)
        AppTheme.set_bgcolor(ft.ThemeMode.LIGHT, snapshot.light_theme_bgcolor)
        await self._persist_theme(snapshot)
        await TtsPreferences.save_language(snapshot.language)
        await TtsPreferences.save_auto_speak_definitions(
            snapshot.auto_speak_definitions
        )
        await TtsPreferences.save_speakers_word_formations(
            snapshot.speakers_word_formations
        )
        await TtsPreferences.save_speakers_word(snapshot.speakers_word)
        await TtsPreferences.save_speakers_definition(snapshot.speakers_definition)
        await LearnPreferences.save_retry_until_correct(snapshot.retry_until_correct)
        await LearnPreferences.save_word_formations_queue_size(
            snapshot.word_formations_queue_size
        )
        await LearnPreferences.save_definitions_queue_size(
            snapshot.definitions_queue_size
        )
        self._sync_controls_from_preferences()
        self._apply_active_theme()

    async def _persist_theme(self, snapshot: _SettingsSnapshot) -> None:
        """Store theme mode and both background shades."""
        storage = get_shared_preferences()
        await self._set_preference(
            storage,
            "theme_mode",
            None if snapshot.theme_mode is None else snapshot.theme_mode.value,
        )
        await storage.set(
            f"{ft.ThemeMode.DARK.value}_theme_slider_value",
            str(snapshot.dark_theme_slider_value),
        )
        await storage.set(
            f"{ft.ThemeMode.LIGHT.value}_theme_slider_value",
            str(snapshot.light_theme_slider_value),
        )
        await self._set_preference(
            storage,
            f"{ft.ThemeMode.DARK.value}_theme_bgcolor",
            snapshot.dark_theme_bgcolor,
        )
        await self._set_preference(
            storage,
            f"{ft.ThemeMode.LIGHT.value}_theme_bgcolor",
            snapshot.light_theme_bgcolor,
        )

    @staticmethod
    async def _set_preference(storage, key: str, value: str | None) -> None:
        if value is None:
            await storage.remove(key)
            return
        await storage.set(key, value)

    def _sync_controls_from_preferences(self) -> None:
        """Show the current theme, TTS, and learn values on this page."""
        self.theme_switch.value = AppTheme.theme_mode == ft.ThemeMode.LIGHT
        self.background_shade_slider.slider.value = AppTheme.get_slider_value()
        self.tts_language_dropdown.value = TtsPreferences.language
        self.tts_auto_speak_switch.value = TtsPreferences.auto_speak_definitions
        self.tts_speakers_word_formations_switch.value = (
            TtsPreferences.speakers_word_formations
        )
        self.tts_speakers_word_switch.value = TtsPreferences.speakers_word
        self.tts_speakers_definition_switch.value = TtsPreferences.speakers_definition
        self.retry_until_correct_switch.value = LearnPreferences.retry_until_correct
        words = self.word_formations_queue_slider
        words.slider.value = LearnPreferences.word_formations_queue_size
        words.label.value = words._format_label(
            LearnPreferences.word_formations_queue_size
        )
        definitions = self.definitions_queue_slider
        definitions.slider.value = LearnPreferences.definitions_queue_size
        definitions.label.value = definitions._format_label(
            LearnPreferences.definitions_queue_size
        )
        self._refresh_speakers_preview()
        self.update_if_mounted()

    def _apply_active_theme(self) -> None:
        """Push the active theme mode and background onto the page."""
        page = self._get_page()
        if page is None:
            return
        if AppTheme.theme_mode is not None:
            page.theme_mode = AppTheme.theme_mode
        if getattr(page, "views", None) is not None:
            AppTheme.apply_to_page(page)
        update = getattr(page, "update", None)
        if callable(update):
            update()

    def on_add_demo_sets_click(self, e):
        page = self._get_page()
        try:
            result = install_demo_sets()
        except FileNotFoundError as exc:
            create_alert_dialog(
                page=page,
                title="Demo sets",
                content=f"Could not find demo files.\n{exc}",
                close_button_text="OK",
            )
            return
        except Exception as exc:
            create_alert_dialog(
                page=page,
                title="Demo sets",
                content=f"Failed to add demo sets.\n{exc}",
                close_button_text="OK",
            )
            return

        if result.added and BodyRegistry.has_home():
            BodyRegistry.get_home().refresh_content()
        if result.added and BodyRegistry.has_export():
            BodyRegistry.get_export().refresh_content()

        create_alert_dialog(
            page=page,
            title="Demo sets",
            content=self._format_install_message(result.added, result.skipped),
            close_button_text="OK",
        )

    @staticmethod
    def _format_install_message(added: list[str], skipped: list[str]) -> str:
        if added and not skipped:
            lines = ["Added all demo sets:"]
            lines.extend(f"• {title}" for title in added)
            return "\n".join(lines)

        if added and skipped:
            lines = ["Added:"]
            lines.extend(f"• {title}" for title in added)
            lines.append("")
            lines.append("Skipped (already present):")
            lines.extend(f"• {title}" for title in skipped)
            return "\n".join(lines)

        if skipped and not added:
            lines = ["No demo sets were added. All are already present:"]
            lines.extend(f"• {title}" for title in skipped)
            return "\n".join(lines)

        return "No demo sets were added."

    def did_mount(self):
        AppTheme.apply_to_page(self._get_page())
        super().did_mount()
        self.background_shade_slider.update_slider_position()
