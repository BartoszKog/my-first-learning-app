"""Per-set settings opened from a learning-set tile menu."""

import flet as ft

from learning_app.data.app_data import get_kind_of_file_and_validate
from learning_app.data.constants import FilesColumns
from learning_app.data.set_settings import (
    clear_set_overrides,
    effective_set_settings,
    enable_set_overrides,
    set_override_value,
)
from learning_app.ui.keyboard_shortcuts import pop_ctrl_b_action, push_ctrl_b_action
from learning_app.ui.layout_metrics import LayoutMetrics
from learning_app.ui.learn_preferences import LearnPreferences
from learning_app.ui.navigation import go_back
from learning_app.ui.routable_screen import RoutableScreenMixin
from learning_app.ui.screens.settings_control import PracticeQueueSlider
from learning_app.ui.tts_preferences import TTS_LANGUAGES, TtsPreferences

_FORM_BORDER_COLOR = ft.Colors.BLUE_GREY_700
_SWITCH_LABEL = ft.TextStyle(size=16)


class SetSettingsMenu(RoutableScreenMixin, ft.Column):
    """Edit the settings stored on one set, or leave them to the app.

    The "Use app settings" switch is on while every override cell for this
    set's kind is empty. Turning it off copies the current app values into
    those cells. Turning it on clears them. Other controls save immediately
    and are disabled while the set follows the app.
    """

    def __init__(self, file_name: str, width: float = 340):
        super().__init__()
        self.expand = True
        self.scroll = ft.ScrollMode.AUTO
        self.alignment = ft.MainAxisAlignment.START
        self.horizontal_alignment = ft.CrossAxisAlignment.CENTER
        self.spacing = 12
        self.file_name = file_name
        self.kind = get_kind_of_file_and_validate(file_name)
        self._form_width = width
        self._ctrl_b_registered = False

        settings = effective_set_settings(file_name)
        use_app = settings.uses_app_defaults
        kind_label = "Word formations" if self.kind == "words" else "Definitions"

        self.heading = ft.Text(
            "Set settings",
            size=18,
            weight=ft.FontWeight.BOLD,
            width=width,
        )
        self.kind_text = ft.Text(kind_label, size=14, width=width)
        self.use_app_settings_switch = ft.Switch(
            label=" Use app settings",
            label_text_style=_SWITCH_LABEL,
            value=use_app,
            on_change=self.on_use_app_settings_change,
        )
        self.use_app_settings_row = ft.Row(
            [self.use_app_settings_switch],
            alignment=ft.MainAxisAlignment.START,
            width=width,
        )
        self.use_app_settings_description = ft.Text(
            "Checked values come from the app. Uncheck to keep different "
            "values for this set. Only settings for this kind of set are shown.",
            size=14,
            width=width,
        )
        self.language_dropdown = ft.Dropdown(
            label="Language",
            value=settings.language,
            options=[
                ft.DropdownOption(key=code, text=label) for code, label in TTS_LANGUAGES
            ],
            width=width,
            border_color=_FORM_BORDER_COLOR,
            disabled=use_app,
            on_select=self.on_language_select,
        )
        self.auto_speak_switch = None
        self.speakers_word_formations_switch = None
        self.speakers_word_switch = None
        self.speakers_definition_switch = None

        option_rows: list[ft.Control] = []
        if self.kind == "words":
            self.speakers_word_formations_switch = self._switch(
                " Word formation speakers",
                settings.speakers_word_formations,
                use_app,
                self.on_speakers_word_formations_change,
            )
            option_rows.append(self._switch_row(self.speakers_word_formations_switch))
        else:
            self.auto_speak_switch = self._switch(
                " Pronounce after Check",
                settings.auto_speak,
                use_app,
                self.on_auto_speak_change,
            )
            self.speakers_word_switch = self._switch(
                " Word speakers",
                settings.speakers_word,
                use_app,
                self.on_speakers_word_change,
            )
            self.speakers_definition_switch = self._switch(
                " Definition speakers",
                settings.speakers_definition,
                use_app,
                self.on_speakers_definition_change,
            )
            option_rows.extend(
                [
                    self._switch_row(self.auto_speak_switch),
                    self._switch_row(self.speakers_word_switch),
                    self._switch_row(self.speakers_definition_switch),
                ]
            )
        self.option_rows = option_rows

        self.retry_switch = self._switch(
            " Retype until correct",
            settings.retry_until_correct,
            use_app,
            self.on_retry_change,
        )
        self.retry_row = self._switch_row(self.retry_switch)

        if self.kind == "words":
            minimum = LearnPreferences.WORD_FORMATIONS_QUEUE_MIN
            maximum = LearnPreferences.WORD_FORMATIONS_QUEUE_MAX
            divisions = maximum - minimum
        else:
            minimum = LearnPreferences.DEFINITIONS_QUEUE_MIN
            maximum = LearnPreferences.DEFINITIONS_QUEUE_MAX
            divisions = maximum - minimum
        self.queue_slider = PracticeQueueSlider(
            title="Queue size",
            minimum=minimum,
            maximum=maximum,
            divisions=divisions,
            initial_value=settings.queue_size,
            on_change=self.on_queue_change,
            width=width,
        )
        self.queue_slider.slider.disabled = use_app

        self.back_button = ft.Button(
            content="Back",
            icon=ft.Icons.ARROW_BACK,
            on_click=self.on_back_click,
            tooltip="Back (Ctrl+B)",
        )
        self.buttons_row = ft.Row(
            [self.back_button],
            alignment=ft.MainAxisAlignment.CENTER,
        )

        self.controls = [
            self.heading,
            self.kind_text,
            self.use_app_settings_row,
            self.use_app_settings_description,
            self.language_dropdown,
            *option_rows,
            self.retry_row,
            self.queue_slider,
            self.buttons_row,
        ]

    def _switch(self, label: str, value: bool, disabled: bool, on_change) -> ft.Switch:
        return ft.Switch(
            label=label,
            label_text_style=_SWITCH_LABEL,
            value=value,
            disabled=disabled,
            on_change=on_change,
        )

    def _switch_row(self, switch: ft.Switch) -> ft.Row:
        return ft.Row(
            [switch],
            alignment=ft.MainAxisAlignment.START,
            width=self._form_width,
        )

    def apply_layout(self, metrics: LayoutMetrics | None = None) -> None:
        metrics = self.resolve_layout_metrics(metrics)
        self._form_width = metrics.form_width
        for control in (
            self.heading,
            self.kind_text,
            self.use_app_settings_description,
            self.use_app_settings_row,
            self.language_dropdown,
            self.retry_row,
            *self.option_rows,
        ):
            control.width = metrics.form_width
        self.queue_slider.apply_layout(metrics.form_width)
        self.update_if_mounted()

    def did_mount(self):
        super().did_mount()
        if not self._ctrl_b_registered:
            push_ctrl_b_action(self.page, self._on_ctrl_b)
            self._ctrl_b_registered = True

    def will_unmount(self):
        if self._ctrl_b_registered:
            pop_ctrl_b_action(self.page, self._on_ctrl_b)
            self._ctrl_b_registered = False

    def _on_ctrl_b(self, e):
        self.on_back_click(e)

    def on_back_click(self, e):
        go_back(e.page)

    def on_use_app_settings_change(self, e):
        if bool(e.control.value):
            clear_set_overrides(self.file_name)
        else:
            enable_set_overrides(self.file_name)
        self._sync_from_catalog()

    def on_language_select(self, e):
        if self.use_app_settings_switch.value:
            return
        language = TtsPreferences.normalize_language(e.control.value)
        e.control.value = language
        set_override_value(self.file_name, FilesColumns.TTS_LANGUAGE.value, language)
        self.update_if_mounted()

    def on_auto_speak_change(self, e):
        self._save_bool(FilesColumns.TTS_AUTO_SPEAK.value, e.control.value)

    def on_speakers_word_formations_change(self, e):
        self._save_bool(FilesColumns.SPEAKERS_WORD_FORMATIONS.value, e.control.value)

    def on_speakers_word_change(self, e):
        self._save_bool(FilesColumns.SPEAKERS_WORD.value, e.control.value)

    def on_speakers_definition_change(self, e):
        self._save_bool(FilesColumns.SPEAKERS_DEFINITION.value, e.control.value)

    def on_retry_change(self, e):
        self._save_bool(FilesColumns.RETRY_UNTIL_CORRECT.value, e.control.value)

    def on_queue_change(self, size: int):
        if self.use_app_settings_switch.value:
            return
        set_override_value(self.file_name, FilesColumns.QUEUE_SIZE.value, str(int(size)))

    def _save_bool(self, column: str, enabled: bool) -> None:
        if self.use_app_settings_switch.value:
            return
        set_override_value(
            self.file_name,
            column,
            "true" if enabled else "false",
        )

    def _sync_from_catalog(self) -> None:
        settings = effective_set_settings(self.file_name)
        use_app = settings.uses_app_defaults
        self.use_app_settings_switch.value = use_app
        self.language_dropdown.value = settings.language
        self.language_dropdown.disabled = use_app
        self._set_switch(self.auto_speak_switch, settings.auto_speak, use_app)
        self._set_switch(
            self.speakers_word_formations_switch,
            settings.speakers_word_formations,
            use_app,
        )
        self._set_switch(self.speakers_word_switch, settings.speakers_word, use_app)
        self._set_switch(
            self.speakers_definition_switch,
            settings.speakers_definition,
            use_app,
        )
        self._set_switch(self.retry_switch, settings.retry_until_correct, use_app)
        self.queue_slider.slider.value = settings.queue_size
        self.queue_slider.slider.disabled = use_app
        self.queue_slider.label.value = self.queue_slider._format_label(settings.queue_size)
        self.update_if_mounted()

    @staticmethod
    def _set_switch(switch: ft.Switch | None, value: bool, disabled: bool) -> None:
        if switch is None:
            return
        switch.value = value
        switch.disabled = disabled
