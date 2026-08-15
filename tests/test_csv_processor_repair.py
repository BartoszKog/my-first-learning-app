"""Tests for ``files.csv`` catalog validation and repair.

These cases cover the recovery paths in ``CSVProcessor.validate_files_csv``
and ``CSVProcessor.repair_files_csv``: extra or missing commas, missing
required columns, an unreadable or absent catalog, and duplicate rows.
Repair must keep existing set entries instead of replacing the catalog with
an empty file.
"""

from pathlib import Path

import pandas as pd

from learning_app.data.constants import FilesColumns
from learning_app.data.csv_processor import CSVProcessor, _recover_catalog_csv
from learning_app.data.file_path_manager import FilePathManager

CATALOG_HEADER = "file_name,title,subtitle,created_at,last_used,use_count"
ROW_ANIMALS = "animals_words.csv,Animals,,2026-01-01T00:00:00+00:00,,0"
ROW_PLANTS = "plants_definitions.csv,Plants,Green,2026-01-02T00:00:00+00:00,,0"


def _write_set(csv_dir: Path, basename: str) -> None:
    (csv_dir / basename).write_text("word,definition\n", encoding="utf-8")


def _write_catalog(csv_dir: Path, text: str) -> Path:
    path = csv_dir / "files.csv"
    path.write_text(text, encoding="utf-8", newline="\n")
    return path


def _seed_two_sets(csv_dir: Path) -> None:
    _write_set(csv_dir, "animals_words.csv")
    _write_set(csv_dir, "plants_definitions.csv")


def _catalog_names() -> list[str]:
    df = pd.read_csv(FilePathManager.get_files_data_path(), index_col=False)
    return df[FilesColumns.FILE_NAME.value].tolist()


def test_validate_keeps_rows_when_one_row_has_extra_comma(isolated_csv_dir: Path):
    """Validate must not treat a stray comma as a shifted index.

    Pandas 3 otherwise uses the first column as the index, so ``file_name``
    becomes the title. With ``index_col=False`` both set basenames stay in
    ``file_name`` and the catalog is still valid.
    """
    _seed_two_sets(isolated_csv_dir)
    _write_catalog(
        isolated_csv_dir,
        f"{CATALOG_HEADER}\n{ROW_ANIMALS},extra\n{ROW_PLANTS}\n",
    )

    validation = CSVProcessor.validate_files_csv()

    assert validation["is_valid"] is True
    names = validation["files_data"][FilesColumns.FILE_NAME.value].tolist()
    assert names == ["animals_words.csv", "plants_definitions.csv"]


def test_repair_keeps_all_sets_when_one_row_has_extra_comma(isolated_csv_dir: Path):
    """Repair after an extra comma must keep every set, not wipe the catalog."""
    _seed_two_sets(isolated_csv_dir)
    _write_catalog(
        isolated_csv_dir,
        f"{CATALOG_HEADER}\n{ROW_ANIMALS},extra\n{ROW_PLANTS}\n",
    )

    result = CSVProcessor.repair_files_csv()

    assert result["success"] is True
    assert _catalog_names() == ["animals_words.csv", "plants_definitions.csv"]
    assert CSVProcessor.validate_files_csv()["is_valid"] is True


def test_repair_restores_rows_when_pandas_shifts_columns(isolated_csv_dir: Path, monkeypatch):
    """If pandas already shifted columns, repair re-parses with csv.reader.

    Simulates the default pandas 3 read (extra fields → first column as index)
    by feeding that shifted frame into repair. File names must come back as
    ``*_words.csv`` / ``*_definitions.csv``, not titles.
    """
    _seed_two_sets(isolated_csv_dir)
    catalog = _write_catalog(
        isolated_csv_dir,
        f"{CATALOG_HEADER}\n{ROW_ANIMALS},extra\n{ROW_PLANTS}\n",
    )
    shifted = pd.read_csv(catalog)
    assert shifted[FilesColumns.FILE_NAME.value].tolist() == ["Animals", "Plants"]

    monkeypatch.setattr(
        CSVProcessor,
        "validate_files_csv",
        staticmethod(lambda: {
            "errors": [
                "Invalid file names in files.csv (must end with '_words.csv' or '_definitions.csv'): Animals, Plants"
            ],
            "warnings": [],
            "is_valid": False,
            "files_data": shifted,
        }),
    )

    result = CSVProcessor.repair_files_csv()

    assert result["success"] is True
    assert any("Recovered catalog rows" in action for action in result["repair_actions"])
    assert _catalog_names() == ["animals_words.csv", "plants_definitions.csv"]


def test_recover_trims_extra_fields_on_one_row(isolated_csv_dir: Path):
    """csv.reader recovery keeps the header width and drops only extra fields."""
    catalog = _write_catalog(
        isolated_csv_dir,
        f"{CATALOG_HEADER}\n{ROW_ANIMALS},extra\n{ROW_PLANTS}\n",
    )

    recovered, actions = _recover_catalog_csv(str(catalog))

    assert recovered is not None
    assert recovered[FilesColumns.FILE_NAME.value].tolist() == [
        "animals_words.csv",
        "plants_definitions.csv",
    ]
    assert any("Trimmed extra fields on 1 row(s)" in action for action in actions)


def test_repair_pads_short_row_and_keeps_all_sets(isolated_csv_dir: Path):
    """A row with too few commas is padded; the other set is not removed."""
    _seed_two_sets(isolated_csv_dir)
    _write_catalog(
        isolated_csv_dir,
        f"{CATALOG_HEADER}\nanimals_words.csv,Animals\n{ROW_PLANTS}\n",
    )

    result = CSVProcessor.repair_files_csv()

    assert result["success"] is True
    assert _catalog_names() == ["animals_words.csv", "plants_definitions.csv"]


def test_repair_adds_missing_subtitle_without_wiping_sets(isolated_csv_dir: Path):
    """Missing ``subtitle`` is filled with empty strings; catalog rows stay."""
    _seed_two_sets(isolated_csv_dir)
    _write_catalog(
        isolated_csv_dir,
        "file_name,title,created_at,last_used,use_count\n"
        "animals_words.csv,Animals,2026-01-01T00:00:00+00:00,,0\n"
        "plants_definitions.csv,Plants,2026-01-02T00:00:00+00:00,,0\n",
    )

    validation = CSVProcessor.validate_files_csv()
    assert validation["is_valid"] is False
    assert any("Missing required columns" in error for error in validation["errors"])

    result = CSVProcessor.repair_files_csv()

    assert result["success"] is True
    assert any("Added missing subtitle column" in action for action in result["repair_actions"])
    assert _catalog_names() == ["animals_words.csv", "plants_definitions.csv"]
    df = pd.read_csv(FilePathManager.get_files_data_path(), index_col=False)
    assert FilesColumns.SUBTITLE.value in df.columns
    assert CSVProcessor.validate_files_csv()["is_valid"] is True


def test_repair_adds_missing_title_from_file_name(isolated_csv_dir: Path):
    """Missing ``title`` is derived from the set basename, not dropped."""
    _write_set(isolated_csv_dir, "animals_words.csv")
    _write_catalog(
        isolated_csv_dir,
        "file_name,subtitle,created_at,last_used,use_count\n"
        "animals_words.csv,,2026-01-01T00:00:00+00:00,,0\n",
    )

    result = CSVProcessor.repair_files_csv()

    assert result["success"] is True
    assert any("Added missing title column from file names" in action for action in result["repair_actions"])
    df = pd.read_csv(FilePathManager.get_files_data_path(), index_col=False)
    assert df.loc[0, FilesColumns.TITLE.value] == "Animals"
    assert CSVProcessor.validate_files_csv()["is_valid"] is True


def test_repair_rebuilds_catalog_when_file_name_column_missing(isolated_csv_dir: Path):
    """Without ``file_name``, rows cannot be matched, so rebuild from set CSVs on disk."""
    _seed_two_sets(isolated_csv_dir)
    _write_catalog(
        isolated_csv_dir,
        "title,subtitle\nAnimals,\nPlants,Green\n",
    )

    result = CSVProcessor.repair_files_csv()

    assert result["success"] is True
    assert any("Rebuilt catalog from set files on disk" in action for action in result["repair_actions"])
    assert set(_catalog_names()) == {"animals_words.csv", "plants_definitions.csv"}
    assert CSVProcessor.validate_files_csv()["is_valid"] is True


def test_repair_leaves_unreadable_file_unchanged(isolated_csv_dir: Path):
    """Bytes that are not UTF-8 text must not be replaced with an empty catalog."""
    path = isolated_csv_dir / "files.csv"
    original = b"\xff\xfe\x00broken"
    path.write_bytes(original)

    validation = CSVProcessor.validate_files_csv()
    assert validation["is_valid"] is False
    assert any("Error loading files.csv" in error for error in validation["errors"])

    result = CSVProcessor.repair_files_csv()

    assert result["success"] is False
    assert any("left the existing file unchanged" in action for action in result["repair_actions"])
    assert path.read_bytes() == original


def test_missing_catalog_is_valid_and_repair_does_not_create_it(isolated_csv_dir: Path):
    """A missing ``files.csv`` is valid; repair must not invent an empty catalog.

    Catalog readers such as ``get_file_names_and_titles`` create the file later.
    """
    catalog = isolated_csv_dir / "files.csv"
    assert not catalog.exists()

    validation = CSVProcessor.validate_files_csv()
    assert validation["is_valid"] is True
    assert validation["files_data"] is None
    assert validation["errors"] == []

    result = CSVProcessor.repair_files_csv()

    assert result["success"] is False
    assert result["repair_actions"] == ["No repairs were made"]
    assert not catalog.exists()


def test_repair_keeps_sets_in_csv_dir_when_removing_duplicates(isolated_csv_dir: Path):
    """Duplicate catalog rows drop extras (keep first); other sets stay listed.

    Missing-file cleanup must resolve paths via ``FilePathManager``, not cwd,
    or every row would look missing and the catalog would be emptied.
    Subtitles that already have text must not produce a fill-empty report.
    """
    _seed_two_sets(isolated_csv_dir)
    _write_catalog(
        isolated_csv_dir,
        f"{CATALOG_HEADER}\n"
        "animals_words.csv,Animals,Sample,2026-01-01T00:00:00+00:00,,0\n"
        "animals_words.csv,Animals,Sample,2026-01-01T00:00:00+00:00,,0\n"
        "plants_definitions.csv,Plants,Green,2026-01-02T00:00:00+00:00,,0\n",
    )

    validation = CSVProcessor.validate_files_csv()
    assert validation["is_valid"] is False
    assert any("Found duplicate file names" in error for error in validation["errors"])

    result = CSVProcessor.repair_files_csv()

    assert result["success"] is True
    assert any("Removed duplicate file entries" in action for action in result["repair_actions"])
    assert not any("Filled empty subtitle" in action for action in result["repair_actions"])
    assert _catalog_names() == ["animals_words.csv", "plants_definitions.csv"]
    assert CSVProcessor.validate_files_csv()["is_valid"] is True


def test_repair_fills_empty_subtitles_only_when_values_are_missing(isolated_csv_dir: Path):
    """NaN subtitle cells are filled and mentioned in the repair report."""
    _write_set(isolated_csv_dir, "animals_words.csv")
    _write_catalog(
        isolated_csv_dir,
        f"{CATALOG_HEADER}\n"
        "animals_words.csv,Animals,,2026-01-01T00:00:00+00:00,,0\n"
        "animals_words.csv,Animals,,2026-01-01T00:00:00+00:00,,0\n",
    )

    result = CSVProcessor.repair_files_csv()

    assert result["success"] is True
    assert any(
        "Filled empty subtitle values with empty strings" in action
        for action in result["repair_actions"]
    )
    df = pd.read_csv(
        FilePathManager.get_files_data_path(),
        index_col=False,
        keep_default_na=False,
    )
    assert df.loc[0, FilesColumns.SUBTITLE.value] == ""
