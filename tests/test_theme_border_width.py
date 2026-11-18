"""Theme border width is chosen when a control is created, not on a later mount."""

import flet as ft
import pandas as pd
import pytest

from learning_app.data.constants import StatsColumns, WordDefinitions
from learning_app.ui.app_theme import AppTheme
from learning_app.ui.components.controls import WordField
from learning_app.ui.screens.word_list_menu import BORDERS, WordContainer


@pytest.fixture
def restore_theme_mode():
    theme_mode = AppTheme.theme_mode
    yield
    AppTheme.theme_mode = theme_mode


def _row(*, good: bool, in_a_row: bool) -> pd.Series:
    return pd.Series(
        {
            WordDefinitions.DEFINITION.value: "control someone",
            WordDefinitions.WORD.value: "keep SB in line",
            StatsColumns.CORRECT_ANSWERS.value: 0,
            StatsColumns.GOOD_ANSWER.value: good,
            StatsColumns.GOOD_ANSWERS_IN_A_ROW.value: in_a_row,
            StatsColumns.WORD_TO_LEARN.value: False,
        }
    )


def _widths(border: ft.Border) -> set[float]:
    return {border.top.width, border.bottom.width, border.left.width, border.right.width}


def test_word_card_uses_the_new_theme_width_on_the_first_build(restore_theme_mode):
    AppTheme.theme_mode = ft.ThemeMode.DARK
    dark_card = WordContainer(_row(good=False, in_a_row=False), 250)
    assert _widths(dark_card.border) == {1.5}
    assert dark_card.border.top.color == ft.Colors.BLUE_GREY_700
    assert dark_card.border is not BORDERS["To learn"]

    AppTheme.theme_mode = ft.ThemeMode.LIGHT
    light_card = WordContainer(_row(good=False, in_a_row=False), 250)
    assert _widths(light_card.border) == {3}
    assert _widths(dark_card.border) == {1.5}
    assert _widths(BORDERS["To learn"]) == {1.5}

    AppTheme.theme_mode = ft.ThemeMode.DARK
    next_dark_card = WordContainer(_row(good=True, in_a_row=True), 250)
    assert _widths(next_dark_card.border) == {1.5}
    assert next_dark_card.border.top.color == ft.Colors.GREEN_ACCENT_700
    assert _widths(light_card.border) == {3}


def test_learned_card_keeps_its_color_at_the_light_width(restore_theme_mode):
    AppTheme.theme_mode = ft.ThemeMode.LIGHT
    card = WordContainer(_row(good=True, in_a_row=False), 250)
    assert _widths(card.border) == {3}
    assert card.border.top.color == ft.Colors.ORANGE_500
    assert card.border is not BORDERS["Learned"]


def test_answer_border_width_follows_the_theme_before_mount(restore_theme_mode):
    AppTheme.theme_mode = ft.ThemeMode.LIGHT
    light_field = WordField(label="Verb")
    light_field.update = lambda: None
    assert light_field.width_border_indicator == 3
    light_field.set_green_border()
    green = light_field.border[ft.ControlState.DEFAULT]
    assert green.side.width == 3
    assert green.side.color == ft.Colors.GREEN

    AppTheme.theme_mode = ft.ThemeMode.DARK
    dark_field = WordField(label="Verb")
    dark_field.update = lambda: None
    assert dark_field.width_border_indicator == 1
    assert light_field.width_border_indicator == 3
    dark_field.set_red_border()
    red = dark_field.border[ft.ControlState.DEFAULT]
    assert red.side.width == 1
    assert red.side.color == ft.Colors.RED
    assert light_field.border[ft.ControlState.FOCUSED].side.width == 3
