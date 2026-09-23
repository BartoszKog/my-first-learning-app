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
from learning_app.ui.tts_preferences import TTS_LANGUAGES, TtsPreferences

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


class SettingsControl(RoutableScreenMixin, ft.Column):
    """Settings shell screen with Appearance, TTS, Learning, and Demo sets.

    Owns the light/dark switch, ``BackgroundShadeSlider``, TTS language,
    auto-speak, word-list speakers, learn-queue retry, and demo-set
    installation. Persistence
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

        self.tts_section_divider = self._section_divider()
        self.learning_section_divider = self._section_divider()
        self.demo_section_divider = self._section_divider()

        self.controls = [
            ft.Container(height=24),
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
            self.appearance_heading,
            self.demo_heading,
            self.tts_heading,
            self.learning_heading,
            self.demo_description,
            self.retry_until_correct_description,
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
        self.tts_speakers_formations_preview.apply_layout(metrics.settings_width)
        self.tts_speakers_definitions_preview.apply_layout(metrics.settings_width)
        self.tts_speakers_divider.apply_layout(metrics.settings_width)

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
