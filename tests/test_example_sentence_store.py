"""Storage and CSV import for definition example sentences."""

import sqlite3
from pathlib import Path

import pandas as pd

from learning_app.data import repository
from learning_app.data.app_data import create_empty_set, load_set, save_set
from learning_app.data.constants import (
    EXAMPLE_SENTENCE_COLUMN,
    Errors,
    PartsOfSpeech,
    StatsColumns,
    Warnings,
    WordDefinitions,
)
from learning_app.data.csv_processor import CSVProcessor
from learning_app.data.file_path_manager import FilePathManager
from learning_app.data.repository import cards_for, ensure_db, get_engine


def _stats() -> dict:
    return {
        StatsColumns.CORRECT_ANSWERS.value: 0,
        StatsColumns.GOOD_ANSWER.value: False,
        StatsColumns.GOOD_ANSWERS_IN_A_ROW.value: False,
        StatsColumns.WORD_TO_LEARN.value: False,
    }


def _definition_row(**overrides) -> dict:
    row = {
        WordDefinitions.DEFINITION.value: "to control someone",
        WordDefinitions.WORD.value: "keep sb in line",
        EXAMPLE_SENTENCE_COLUMN: "I { keep } him {in line}.",
        **_stats(),
    }
    row.update(overrides)
    return row


def test_round_trip_normalizes_example_sentence(isolated_csv_dir: Path):
    save_set(pd.DataFrame([_definition_row()]), "idiom_definitions.csv")

    loaded = load_set("idiom_definitions.csv")
    assert loaded.loc[0, EXAMPLE_SENTENCE_COLUMN] == "I {keep} him {in line}."
    assert cards_for("idiom_definitions.csv")[0].example_sentence == "I {keep} him {in line}."


def test_save_without_the_column_clears_a_stored_example(isolated_csv_dir: Path):
    save_set(pd.DataFrame([_definition_row()]), "idiom_definitions.csv")
    bare = {
        WordDefinitions.DEFINITION.value: "to control someone",
        WordDefinitions.WORD.value: "keep sb in line",
        **_stats(),
    }
    save_set(pd.DataFrame([bare]), "idiom_definitions.csv")

    assert cards_for("idiom_definitions.csv")[0].example_sentence == ""
    loaded = load_set("idiom_definitions.csv")
    assert pd.isna(loaded.loc[0, EXAMPLE_SENTENCE_COLUMN])


def test_words_frame_omits_example_sentence(isolated_csv_dir: Path):
    row = {
        PartsOfSpeech.VERB.value: "go",
        PartsOfSpeech.PERSON.value: "walker",
        PartsOfSpeech.THING.value: "path",
        PartsOfSpeech.ADJECTIVE.value: "quick",
        PartsOfSpeech.ADVERB.value: "",
        **_stats(),
    }
    save_set(pd.DataFrame([row]), "plain_words.csv")

    loaded = load_set("plain_words.csv")
    assert EXAMPLE_SENTENCE_COLUMN not in loaded.columns
    assert cards_for("plain_words.csv")[0].example_sentence == ""
    assert EXAMPLE_SENTENCE_COLUMN in create_empty_set("definitions").columns
    assert EXAMPLE_SENTENCE_COLUMN not in create_empty_set("words").columns


def test_ensure_db_adds_example_sentence_to_an_existing_card_table(isolated_csv_dir: Path):
    db_path = FilePathManager.get_db_path()
    with sqlite3.connect(db_path) as connection:
        connection.execute(
            """
            CREATE TABLE card (
                id TEXT PRIMARY KEY,
                set_id TEXT NOT NULL,
                position INTEGER NOT NULL,
                verb TEXT NOT NULL DEFAULT '',
                person TEXT NOT NULL DEFAULT '',
                thing TEXT NOT NULL DEFAULT '',
                adjective TEXT NOT NULL DEFAULT '',
                adverb TEXT NOT NULL DEFAULT '',
                definition TEXT NOT NULL DEFAULT '',
                word TEXT NOT NULL DEFAULT '',
                correct_answers INTEGER NOT NULL DEFAULT 0,
                good_answer INTEGER NOT NULL DEFAULT 0,
                good_answers_in_a_row INTEGER NOT NULL DEFAULT 0,
                word_to_learn INTEGER NOT NULL DEFAULT 0,
                checks INTEGER NOT NULL DEFAULT 0
            )
            """
        )

    ensure_db()
    with get_engine().connect() as connection:
        names = [row[1] for row in connection.exec_driver_sql("PRAGMA table_info(card)")]
    assert names.count(EXAMPLE_SENTENCE_COLUMN) == 1

    repository._ready_path = None
    ensure_db()
    with get_engine().connect() as connection:
        names = [row[1] for row in connection.exec_driver_sql("PRAGMA table_info(card)")]
    assert names.count(EXAMPLE_SENTENCE_COLUMN) == 1


def test_ensure_db_adds_example_mode_to_an_existing_set_table(isolated_csv_dir: Path):
    db_path = FilePathManager.get_db_path()
    with sqlite3.connect(db_path) as connection:
        connection.execute(
            """
            CREATE TABLE learning_set (
                id TEXT PRIMARY KEY,
                kind TEXT NOT NULL,
                title TEXT NOT NULL,
                subtitle TEXT NOT NULL DEFAULT '',
                created_at DATETIME NOT NULL,
                last_used DATETIME,
                use_count INTEGER NOT NULL DEFAULT 0,
                source_file_name TEXT UNIQUE,
                tts_language TEXT,
                tts_auto_speak BOOLEAN,
                speakers_word_formations BOOLEAN,
                speakers_word BOOLEAN,
                speakers_definition BOOLEAN,
                retry_until_correct BOOLEAN,
                queue_size INTEGER
            )
            """
        )

    ensure_db()
    with get_engine().connect() as connection:
        names = [
            row[1] for row in connection.exec_driver_sql("PRAGMA table_info(learning_set)")
        ]
    assert names.count("example_mode") == 1
    assert names.count("speakers_example") == 1


def test_demo_definition_sets_have_valid_examples():
    from learning_app.data.demo_sets import DEMO_SETS, resolve_demo_asset_path
    from learning_app.data.example_sentence import example_sentence_error

    for demo in DEMO_SETS:
        if not demo["file_name"].endswith("_definitions.csv"):
            continue
        frame = pd.read_csv(resolve_demo_asset_path(demo["asset_relative"]), index_col=0)
        examples = frame[EXAMPLE_SENTENCE_COLUMN]
        assert examples.notna().all()
        for example in examples:
            assert example_sentence_error(example) is None, example


def _write_definitions(csv_dir: Path, name: str, body: str) -> Path:
    path = csv_dir / name
    path.write_text(body, encoding="utf-8", newline="\n")
    return path


def test_validate_accepts_an_optional_example_column(isolated_csv_dir: Path):
    path = _write_definitions(
        isolated_csv_dir,
        "idiom_definitions.csv",
        ",definition,word,example_sentence\n"
        '0,to control someone,keep sb in line,"I {keep} him {in line}."\n'
        "1,a path,way,\n",
    )

    result = CSVProcessor.validate_file(str(path))

    assert result["is_valid"] is True
    assert result["data_type"] == "definitions"
    assert Warnings.UNNECESSARY_COLUMNS.value not in result["warnings"]


def test_validate_accepts_definitions_without_the_example_column(isolated_csv_dir: Path):
    path = _write_definitions(
        isolated_csv_dir,
        "plain_definitions.csv",
        ",definition,word\n0,a path,way\n",
    )

    result = CSVProcessor.validate_file(str(path))

    assert result["is_valid"] is True
    assert result["errors"] == []


def test_validate_rejects_a_broken_example_sentence(isolated_csv_dir: Path):
    path = _write_definitions(
        isolated_csv_dir,
        "broken_definitions.csv",
        ",definition,word,example_sentence\n"
        '0,to control someone,keep sb in line,"I {keep him."\n',
    )

    result = CSVProcessor.validate_file(str(path))

    assert result["is_valid"] is False
    assert result["errors"] == [
        f"{Errors.INVALID_EXAMPLE_SENTENCE.value} Row 0: Braces must come in pairs."
    ]


def test_import_keeps_and_normalizes_the_example(isolated_csv_dir: Path):
    path = _write_definitions(
        isolated_csv_dir,
        "idiom_definitions.csv",
        ",definition,word,example_sentence\n"
        '0,to control someone,keep sb in line,"I { keep } him {in line}."\n',
    )

    CSVProcessor.save_set_with_no_specific_actions(
        str(path),
        "idiom_definitions.csv",
        "Idiom",
        "",
        False,
    )

    loaded = load_set("idiom_definitions.csv")
    assert loaded.loc[0, EXAMPLE_SENTENCE_COLUMN] == "I {keep} him {in line}."
