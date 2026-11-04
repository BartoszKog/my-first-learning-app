"""Per-set settings opened from a learning-set tile menu."""

import flet as ft

from learning_app.data.app_data import get_kind_of_file_and_validate
from learning_app.data.constants import FilesColumns
from learning_app.data.set_settings import (
    catalog_title,
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
_MUTED_LABEL = ft.Colors.BLUE_GREY_400
_SWITCH_LABEL = ft.TextStyle(size=16)
_CARD_PADDING = 12


class SetSettingsMenu(RoutableScreenMixin, ft.Column):
    """Edit the settings stored on one set, or leave them to the app.

    The "Use app settings" switch is on while every override cell for this
    set's kind is empty. Turning it off copies the current app values into
    those cells. Turning it on clears them. Other controls save immediately
    and are disabled while the set follows the app.

    Layout: top bar with back ``IconButton``, set title, and kind chip;
    settings grouped into bordered Source / Text to speech / Learning cards.
    """

    def __init__(self, file_name: str, width: float = 340):
        super().__init__()
        self.expand = True
        self.scroll = ft.ScrollMode.AUTO
        self.alignment = ft.MainAxisAlignment.START
        self.horizontal_alignment = ft.CrossAxisAlignment.CENTER
        self.spacing = 0
        self.file_name = file_name
        self.kind = get_kind_of_file_and_validate(file_name)
        self._form_width = width
        self._ctrl_b_registered = False

        settings = effective_set_settings(file_name)
        use_app = settings.uses_app_defaults
        kind_label = "Word formations" if self.kind == "words" else "Definitions"
        set_title = catalog_title(file_name)
        inner = self._inner_width(width)

        self.back_button = ft.IconButton(
            icon=ft.Icons.ARROW_BACK,
            on_click=self.on_back_click,
            tooltip="Back (Ctrl+B)",
            icon_size=22,
        )
        self.heading = ft.Text(
            "Set settings",
            size=16,
            weight=ft.FontWeight.BOLD,
        )
        self.set_title_text = ft.Text(
            set_title,
            size=14,
            color=_MUTED_LABEL,
            max_lines=1,
            overflow=ft.TextOverflow.ELLIPSIS,
        )
        self.kind_text = ft.Text(kind_label, size=12)
        self.kind_chip = ft.Chip(
            label=self.kind_text,
            leading=ft.Icon(ft.Icons.CATEGORY_OUTLINED, size=16),
            show_checkmark=False,
        )
        self.top_bar = ft.Row(
            [
                self.back_button,
                ft.Column(
                    [self.heading, self.set_title_text],
                    spacing=0,
                    expand=True,
                    alignment=ft.MainAxisAlignment.CENTER,
                ),
                self.kind_chip,
            ],
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            width=width,
            spacing=4,
        )

        self.use_app_settings_switch = ft.Switch(
            label=" Use app settings",
            label_text_style=_SWITCH_LABEL,
            value=use_app,
            on_change=self.on_use_app_settings_change,
        )
        self.use_app_settings_row = ft.Row(
            [self.use_app_settings_switch],
            alignment=ft.MainAxisAlignment.START,
            width=inner,
        )
        self.use_app_settings_description = ft.Text(
            "Checked values come from the app. Uncheck to keep different "
            "values for this set. Only settings for this kind of set are shown.",
            size=14,
            width=inner,
        )

        self.tts_description = ft.Text(
            f"Options for {kind_label.lower()} sets.",
            size=14,
            width=inner,
        )
        self.language_dropdown = ft.Dropdown(
            label="Language",
            value=settings.language,
            options=[
                ft.DropdownOption(key=code, text=label) for code, label in TTS_LANGUAGES
            ],
            width=inner,
            border=ft.OutlineInputBorder(
                side=ft.BorderSide(color=_FORM_BORDER_COLOR),
            ),
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
            width=inner,
        )
        self.queue_slider.slider.disabled = use_app

        self.source_heading = self._section_heading("Source", inner)
        self.tts_heading = self._section_heading("Text to speech", inner)
        self.learning_heading = self._section_heading("Learning", inner)

        self.source_card = self._section_card(
            [
                self.source_heading,
                self.use_app_settings_row,
                self.use_app_settings_description,
            ],
            width,
            inner,
        )
        self.tts_card = self._section_card(
            [
                self.tts_heading,
                self.tts_description,
                self.language_dropdown,
                *option_rows,
            ],
            width,
            inner,
        )
        self.learning_card = self._section_card(
            [
                self.learning_heading,
                self.retry_row,
                self.queue_slider,
            ],
            width,
            inner,
        )

        self.controls = [
            self.top_bar,
            ft.Container(height=16),
            self.source_card,
            ft.Container(height=12),
            self.tts_card,
            ft.Container(height=12),
            self.learning_card,
            ft.Container(height=24),
        ]

    @staticmethod
    def _inner_width(form_width: float) -> float:
        return max(0, form_width - 2 * _CARD_PADDING)

    @staticmethod
    def _section_heading(text: str, width: float) -> ft.Text:
        return ft.Text(text, size=18, weight=ft.FontWeight.BOLD, width=width)

    @staticmethod
    def _section_card(
        children: list[ft.Control], form_width: float, inner_width: float
    ) -> ft.Container:
        return ft.Container(
            content=ft.Column(children, spacing=12, width=inner_width),
            padding=_CARD_PADDING,
            border=ft.Border.all(1.5, _FORM_BORDER_COLOR),
            border_radius=8,
            width=form_width,
        )

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
            width=self._inner_width(self._form_width),
        )

    def apply_layout(self, metrics: LayoutMetrics | None = None) -> None:
        metrics = self.resolve_layout_metrics(metrics)
        self._form_width = metrics.form_width
        inner = self._inner_width(metrics.form_width)
        self.top_bar.width = metrics.form_width
        for card in (self.source_card, self.tts_card, self.learning_card):
            card.width = metrics.form_width
            card.content.width = inner
        for control in (
            self.source_heading,
            self.tts_heading,
            self.learning_heading,
            self.use_app_settings_description,
            self.use_app_settings_row,
            self.tts_description,
            self.language_dropdown,
            self.retry_row,
            *self.option_rows,
        ):
            control.width = inner
        self.queue_slider.apply_layout(inner)
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
