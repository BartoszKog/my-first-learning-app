"""Hardest filter chip in WordListMenu: ranking, stats footer, and empty state."""

from types import SimpleNamespace

import flet as ft
import pandas as pd

from learning_app.data.app_data import (
    AppData,
    add_new_file,
    save_set,
    set_default_progress,
)
from learning_app.data.constants import (
    CHECKS_COLUMN,
    EXAMPLE_SENTENCE_COLUMN,
    PartsOfSpeech,
    StatsColumns,
    WordDefinitions,
)
from learning_app.ui.screens.word_list_menu import (
    COLORS_CHECKS,
    WordContainer,
    WordListMenu,
    _card_mistake_stats,
)


def _definitions_frame(rows: list[dict[str, object]]) -> pd.DataFrame:
    normalized = []
    for item in rows:
        normalized.append(
            {
                WordDefinitions.DEFINITION.value: item["definition"],
                WordDefinitions.WORD.value: item["word"],
                EXAMPLE_SENTENCE_COLUMN: item.get("example", ""),
                StatsColumns.CORRECT_ANSWERS.value: item.get("correct", 0),
                StatsColumns.GOOD_ANSWERS_IN_A_ROW.value: item.get("in_a_row", False),
                StatsColumns.GOOD_ANSWER.value: item.get("good", False),
                StatsColumns.WORD_TO_LEARN.value: item.get("to_learn", False),
                CHECKS_COLUMN: item.get("checks", 0),
            }
        )
    return pd.DataFrame(normalized)


def _words_frame(rows: list[dict[str, object]]) -> pd.DataFrame:
    normalized = []
    for item in rows:
        normalized.append(
            {
                PartsOfSpeech.VERB.value: item.get("verb", ""),
                PartsOfSpeech.PERSON.value: item.get("person", ""),
                PartsOfSpeech.THING.value: item.get("thing", ""),
                PartsOfSpeech.ADJECTIVE.value: item.get("adjective", ""),
                PartsOfSpeech.ADVERB.value: item.get("adverb", ""),
                StatsColumns.CORRECT_ANSWERS.value: item.get("correct", 0),
                StatsColumns.GOOD_ANSWERS_IN_A_ROW.value: item.get("in_a_row", False),
                StatsColumns.GOOD_ANSWER.value: item.get("good", False),
                StatsColumns.WORD_TO_LEARN.value: item.get("to_learn", False),
                CHECKS_COLUMN: item.get("checks", 0),
            }
        )
    return pd.DataFrame(normalized)


def _select_chip(menu: WordListMenu, label: str) -> None:
    chip = menu.dict_filter_chips[label]
    chip.selected = True
    chip.on_select(SimpleNamespace(control=chip))


def _card_word(card: WordContainer) -> str:
    column = card.content
    assert isinstance(column, ft.Column)
    for control in column.controls:
        if isinstance(control, ft.Row) and control.controls[0].value.strip() in {"Word", "Verb"}:
            return control.controls[1].value
    raise AssertionError("No Word/Verb row found on card")


def _card_footer(card: WordContainer) -> str | None:
    column = card.content
    assert isinstance(column, ft.Column)
    footers = [control for control in column.controls if isinstance(control, ft.Container)]
    if not footers:
        return None
    assert len(footers) == 1
    assert isinstance(footers[0].content, ft.Text)
    return footers[0].content.value


def test_hardest_chip_is_positioned_after_previous_session():
    file_name = "Order_definitions.csv"
    save_set(
        _definitions_frame([{"definition": "d1", "word": "w1"}]),
        file_name,
    )
    add_new_file(file_name, "Order")

    menu = WordListMenu(file_name)
    labels = [chip.label.value for chip in menu.filter_chips_row.content.controls]

    assert labels == ["All", "Previous session", "Hardest", "Learned", "To learn", "Known"]
    assert COLORS_CHECKS["Hardest"] == ft.Colors.PURPLE_ACCENT_200
    assert menu.dict_filter_chips["Hardest"].check_color == ft.Colors.PURPLE_ACCENT_200


def test_hardest_ranks_by_mistakes_then_lower_accuracy_and_includes_known():
    file_name = "Rank_definitions.csv"
    save_set(
        _definitions_frame(
            [
                # 0 mistakes, To learn -> excluded
                {"definition": "d0", "word": "unseen", "checks": 0, "correct": 0},
                # 1 mistake, 75% correct, Known -> included, last among 1-mistake cards
                {
                    "definition": "d1",
                    "word": "known_one_miss",
                    "checks": 4,
                    "correct": 3,
                    "good": True,
                    "in_a_row": True,
                    "to_learn": False,
                },
                # 1 mistake, 50% correct (first position) -> tie-break preserves order
                {
                    "definition": "d2",
                    "word": "tie_first",
                    "checks": 2,
                    "correct": 1,
                    "good": True,
                    "in_a_row": False,
                    "to_learn": True,
                },
                # 3 mistakes, 40% correct -> #1 hardest
                {
                    "definition": "d3",
                    "word": "most_mistakes",
                    "checks": 5,
                    "correct": 2,
                    "good": False,
                    "in_a_row": False,
                    "to_learn": True,
                },
                # 0 mistakes, Known -> excluded
                {
                    "definition": "d4",
                    "word": "flawless_known",
                    "checks": 2,
                    "correct": 2,
                    "good": True,
                    "in_a_row": True,
                    "to_learn": False,
                },
                # 1 mistake, 50% correct (second position) -> stays after tie_first
                {
                    "definition": "d5",
                    "word": "tie_second",
                    "checks": 2,
                    "correct": 1,
                    "good": False,
                    "in_a_row": False,
                    "to_learn": True,
                },
                # 1 mistake, 0% correct -> beats 50% and 75% on accuracy tie-break
                {
                    "definition": "d6",
                    "word": "zero_accuracy",
                    "checks": 1,
                    "correct": 0,
                    "good": False,
                    "in_a_row": False,
                    "to_learn": True,
                },
            ]
        ),
        file_name,
    )
    add_new_file(file_name, "Rank")

    menu = WordListMenu(file_name)
    menu.bp.update = lambda: None
    _select_chip(menu, "Hardest")

    cards = menu.lv.controls
    assert all(isinstance(card, WordContainer) for card in cards)
    assert [_card_word(card) for card in cards] == [
        "most_mistakes",
        "zero_accuracy",
        "tie_first",
        "tie_second",
        "known_one_miss",
    ]
    assert [_card_footer(card) for card in cards] == [
        "3 mistakes · 40% correct",
        "1 mistake · 0% correct",
        "1 mistake · 50% correct",
        "1 mistake · 50% correct",
        "1 mistake · 75% correct",
    ]
    assert cards[-1].is_known()
    assert cards[-1].border.top.color == ft.Colors.GREEN_ACCENT_700


def test_mistake_footer_appears_only_in_hardest_view():
    file_name = "FooterScope_words.csv"
    save_set(
        _words_frame(
            [
                {
                    "verb": "create",
                    "person": "creator",
                    "checks": 5,
                    "correct": 2,
                    "good": False,
                    "in_a_row": False,
                    "to_learn": True,
                },
                {
                    "verb": "act",
                    "person": "actor",
                    "checks": 3,
                    "correct": 2,
                    "good": True,
                    "in_a_row": True,
                    "to_learn": False,
                },
            ]
        ),
        file_name,
    )
    add_new_file(file_name, "FooterScope")

    AppData.last_group_of_indexes = [0, 1]
    try:
        menu = WordListMenu(file_name)
        _select_chip(menu, "Hardest")
        assert [_card_word(c) for c in menu.lv.controls] == ["create", "act"]
        assert [_card_footer(c) for c in menu.lv.controls] == [
            "3 mistakes · 40% correct",
            "1 mistake · 67% correct",
        ]

        for other_chip in ("All", "Previous session", "Learned", "Known"):
            _select_chip(menu, other_chip)
            assert menu.lv.controls
            assert all(_card_footer(c) is None for c in menu.lv.controls)
    finally:
        AppData.delete_last_group_of_indexes()


def test_hardest_empty_state_appears_and_updates_across_answers_and_reset():
    file_name = "EmptyHardest_definitions.csv"
    save_set(
        _definitions_frame(
            [
                {"definition": "d1", "word": "alpha", "checks": 0, "correct": 0},
                {"definition": "d2", "word": "beta", "checks": 1, "correct": 1, "good": True},
            ]
        ),
        file_name,
    )
    add_new_file(file_name, "EmptyHardest")

    menu = WordListMenu(file_name)
    menu.bp.update = lambda: None
    _select_chip(menu, "Hardest")

    assert len(menu.lv.controls) == 1
    empty = menu.lv.controls[0]
    assert isinstance(empty, ft.Container)
    assert not isinstance(empty, WordContainer)
    assert isinstance(empty.content, ft.Text)
    assert empty.content.value == "No mistakes yet."
    assert empty.alignment == ft.Alignment.CENTER

    # Record one wrong answer and refresh while Hardest stays selected.
    session = AppData(file_name)
    session.current_word_index = 0
    session.current_word_row = session.words.loc[0]
    session.bad_answer_at_current_row()

    menu.refresh_content()
    assert len(menu.lv.controls) == 1
    assert isinstance(menu.lv.controls[0], WordContainer)
    assert _card_word(menu.lv.controls[0]) == "alpha"
    assert _card_footer(menu.lv.controls[0]) == "1 mistake · 0% correct"

    # Resetting progress returns to the empty-state message.
    set_default_progress(file_name)
    menu.refresh_content()
    assert len(menu.lv.controls) == 1
    assert not isinstance(menu.lv.controls[0], WordContainer)
    assert menu.lv.controls[0].content.value == "No mistakes yet."


def test_missing_or_inconsistent_checks_stay_safe():
    row_no_checks = pd.Series(
        {
            WordDefinitions.DEFINITION.value: "d",
            WordDefinitions.WORD.value: "w",
            StatsColumns.CORRECT_ANSWERS.value: 3,
            StatsColumns.GOOD_ANSWER.value: True,
            StatsColumns.GOOD_ANSWERS_IN_A_ROW.value: True,
            StatsColumns.WORD_TO_LEARN.value: False,
        }
    )
    assert _card_mistake_stats(row_no_checks) == (0, 3, 0)
    card = WordContainer(row_no_checks, 250, show_mistake_stats=True)
    assert _card_footer(card) is None

    row_nan_checks = row_no_checks.copy()
    row_nan_checks[CHECKS_COLUMN] = pd.NA
    assert _card_mistake_stats(row_nan_checks) == (0, 3, 0)

    row_inconsistent = row_no_checks.copy()
    row_inconsistent[CHECKS_COLUMN] = 1
    assert _card_mistake_stats(row_inconsistent) == (0, 3, 1)
