"""Tests for catalog tile progress counts from set statistics."""

from pathlib import Path

import pandas as pd

from learning_app.data.app_data import create_empty_set, get_set_learn_progress, save_set
from learning_app.data.constants import PartsOfSpeech, StatsColumns, WordDefinitions


def _words_row(*, known: bool = False, learned: bool = False, to_learn: bool = False) -> dict:
    if known:
        good_answer, in_a_row, word_to_learn = True, True, False
    elif learned:
        good_answer, in_a_row, word_to_learn = True, False, False
    elif to_learn:
        good_answer, in_a_row, word_to_learn = False, False, True
    else:
        good_answer, in_a_row, word_to_learn = False, False, False
    return {
        PartsOfSpeech.VERB.value: "go",
        PartsOfSpeech.PERSON.value: "walker",
        PartsOfSpeech.THING.value: "path",
        PartsOfSpeech.ADJECTIVE.value: "quick",
        PartsOfSpeech.ADVERB.value: "quickly",
        StatsColumns.CORRECT_ANSWERS.value: 2 if known else 1 if learned else 0,
        StatsColumns.GOOD_ANSWER.value: good_answer,
        StatsColumns.GOOD_ANSWERS_IN_A_ROW.value: in_a_row,
        StatsColumns.WORD_TO_LEARN.value: word_to_learn,
    }


def test_get_set_learn_progress_counts_known_rows(isolated_csv_dir: Path):
    df = pd.concat(
        [
            create_empty_set("words"),
            pd.DataFrame(
                [
                    _words_row(known=True),
                    _words_row(to_learn=True),
                    _words_row(),
                ]
            ),
        ],
        ignore_index=True,
    )
    save_set(df, "sample_words.csv")

    # 1 Known + 1 queued (0.25) + 1 unverified (0) → 5/12
    assert get_set_learn_progress("sample_words.csv") == (5, 12)


def test_get_set_learn_progress_learned_counts_as_quarter(isolated_csv_dir: Path):
    df = pd.concat(
        [
            create_empty_set("words"),
            pd.DataFrame(
                [
                    _words_row(learned=True),
                    _words_row(learned=True),
                    _words_row(),
                    _words_row(),
                ]
            ),
        ],
        ignore_index=True,
    )
    save_set(df, "learned_words.csv")

    # Two Learned (0.25 each) + two unverified → 2/16
    assert get_set_learn_progress("learned_words.csv") == (2, 16)


def test_get_set_learn_progress_all_known_is_complete(isolated_csv_dir: Path):
    df = pd.concat(
        [
            create_empty_set("definitions"),
            pd.DataFrame(
                [
                    {
                        WordDefinitions.DEFINITION.value: "a path",
                        WordDefinitions.WORD.value: "way",
                        StatsColumns.CORRECT_ANSWERS.value: 2,
                        StatsColumns.GOOD_ANSWER.value: True,
                        StatsColumns.GOOD_ANSWERS_IN_A_ROW.value: True,
                        StatsColumns.WORD_TO_LEARN.value: False,
                    }
                ]
            ),
        ],
        ignore_index=True,
    )
    save_set(df, "sample_definitions.csv")

    assert get_set_learn_progress("sample_definitions.csv") == (4, 4)


def test_get_set_learn_progress_empty_set(isolated_csv_dir: Path):
    save_set(create_empty_set("words"), "empty_words.csv")

    assert get_set_learn_progress("empty_words.csv") == (0, 0)


def test_get_set_learn_progress_missing_file(isolated_csv_dir: Path):
    assert get_set_learn_progress("missing_words.csv") == (0, 0)


def test_get_set_learn_progress_missing_stats_columns(isolated_csv_dir: Path):
    pd.DataFrame({"verb": ["go"], "person": ["walker"]}).to_csv(
        isolated_csv_dir / "nostats_words.csv",
        index=True,
    )

    assert get_set_learn_progress("nostats_words.csv") == (0, 4)


def test_load_set_keeps_numeric_looking_content_as_strings(isolated_csv_dir: Path):
    from learning_app.data.app_data import load_set

    df = pd.concat(
        [
            create_empty_set("definitions"),
            pd.DataFrame(
                [
                    {
                        WordDefinitions.DEFINITION.value: "e",
                        WordDefinitions.WORD.value: "123",
                        StatsColumns.CORRECT_ANSWERS.value: 0,
                        StatsColumns.GOOD_ANSWER.value: False,
                        StatsColumns.GOOD_ANSWERS_IN_A_ROW.value: False,
                        StatsColumns.WORD_TO_LEARN.value: False,
                    }
                ]
            ),
        ],
        ignore_index=True,
    )
    save_set(df, "numeric_definitions.csv")

    loaded = load_set("numeric_definitions.csv")
    word = loaded.loc[0, WordDefinitions.WORD.value]
    assert word == "123"
    assert isinstance(word, str)


def test_load_set_keeps_na_sentinel_words_as_strings(isolated_csv_dir: Path):
    from learning_app.data.app_data import load_set

    df = pd.concat(
        [
            create_empty_set("definitions"),
            pd.DataFrame(
                [
                    {
                        WordDefinitions.DEFINITION.value: "None",
                        WordDefinitions.WORD.value: "nan",
                        StatsColumns.CORRECT_ANSWERS.value: 0,
                        StatsColumns.GOOD_ANSWER.value: False,
                        StatsColumns.GOOD_ANSWERS_IN_A_ROW.value: False,
                        StatsColumns.WORD_TO_LEARN.value: False,
                    }
                ]
            ),
        ],
        ignore_index=True,
    )
    save_set(df, "sentinel_definitions.csv")

    loaded = load_set("sentinel_definitions.csv")
    assert loaded.loc[0, WordDefinitions.WORD.value] == "nan"
    assert loaded.loc[0, WordDefinitions.DEFINITION.value] == "None"
    assert isinstance(loaded.loc[0, WordDefinitions.WORD.value], str)
