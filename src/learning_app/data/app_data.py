"""Catalog CRUD, set load/save helpers, and in-memory learning sessions.

Module-level functions manage ``files.csv`` and set CSVs on disk through
``FilePathManager``. ``AppData`` loads one set for a learn session, draws
practice groups from statistics columns, and persists answers with ``save_set``.
"""

import os
import random as rd
from datetime import datetime, timedelta, timezone

import pandas as pd

from learning_app.data.constants import FilesColumns, PartsOfSpeech, SetSortMode, StatsColumns, WordDefinitions
from learning_app.data.file_path_manager import FilePathManager

_CATALOG_COLUMN_ORDER = [
    FilesColumns.FILE_NAME.value,
    FilesColumns.TITLE.value,
    FilesColumns.SUBTITLE.value,
    FilesColumns.CREATED_AT.value,
    FilesColumns.LAST_USED.value,
    FilesColumns.USE_COUNT.value,
]


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def ensure_files_catalog_columns(df: pd.DataFrame | None = None, *, persist: bool = True) -> pd.DataFrame:
    """Ensure catalog DataFrame has usage/creation columns; optionally rewrite CSV.

    Missing columns are added with defaults. Rows missing ``created_at`` get
    stable timestamps in existing row order so creation sort matches historical
    append order. Older catalogs without usage fields get empty ``last_used``
    and ``use_count`` of ``0``.

    Args:
        df: Catalog table to migrate. When ``None``, loads ``files.csv`` (or
            creates an empty catalog first).
        persist: When ``True`` and columns/values changed, write ``files.csv``.

    Returns:
        Catalog DataFrame with the full column set.
    """
    files_data_path = FilePathManager.get_files_data_path()

    if df is None:
        if not os.path.exists(files_data_path):
            generate_empty_files_data()
        df = pd.read_csv(files_data_path)

    changed = False
    base_created = datetime(2000, 1, 1, tzinfo=timezone.utc)

    if FilesColumns.CREATED_AT.value not in df.columns:
        df[FilesColumns.CREATED_AT.value] = [
            (base_created + timedelta(seconds=i)).isoformat() for i in range(len(df))
        ]
        changed = True
    else:
        for position, i in enumerate(df.index):
            value = df.at[i, FilesColumns.CREATED_AT.value]
            if pd.isna(value) or str(value).strip() == "":
                df.at[i, FilesColumns.CREATED_AT.value] = (
                    base_created + timedelta(seconds=position)
                ).isoformat()
                changed = True

    if FilesColumns.LAST_USED.value not in df.columns:
        df[FilesColumns.LAST_USED.value] = ""
        changed = True
    else:
        df[FilesColumns.LAST_USED.value] = df[FilesColumns.LAST_USED.value].apply(
            lambda x: "" if pd.isna(x) else str(x)
        )

    if FilesColumns.USE_COUNT.value not in df.columns:
        df[FilesColumns.USE_COUNT.value] = 0
        changed = True
    else:
        df[FilesColumns.USE_COUNT.value] = (
            pd.to_numeric(df[FilesColumns.USE_COUNT.value], errors="coerce").fillna(0).astype(int)
        )

    ordered = [col for col in _CATALOG_COLUMN_ORDER if col in df.columns]
    ordered.extend(col for col in df.columns if col not in _CATALOG_COLUMN_ORDER)
    df = df.reindex(columns=ordered)

    if persist and changed:
        df.to_csv(files_data_path, index=False)

    return df


def sort_catalog_entries(entries: list[dict], sort_mode: SetSortMode) -> list[dict]:
    """Return catalog entry dicts ordered by ``sort_mode``."""
    if sort_mode is SetSortMode.LAST_USED:
        used = [e for e in entries if e.get(FilesColumns.LAST_USED.value)]
        unused = [e for e in entries if not e.get(FilesColumns.LAST_USED.value)]
        used.sort(
            key=lambda e: (
                e[FilesColumns.LAST_USED.value],
                e.get(FilesColumns.CREATED_AT.value) or "",
                (e.get(FilesColumns.TITLE.value) or "").lower(),
            ),
            reverse=True,
        )
        unused.sort(
            key=lambda e: (
                e.get(FilesColumns.CREATED_AT.value) or "",
                (e.get(FilesColumns.TITLE.value) or "").lower(),
            )
        )
        return used + unused

    if sort_mode is SetSortMode.CREATED:
        return sorted(
            entries,
            key=lambda e: (
                e.get(FilesColumns.CREATED_AT.value) or "",
                (e.get(FilesColumns.TITLE.value) or "").lower(),
            ),
            reverse=True,
        )

    if sort_mode is SetSortMode.TITLE:
        return sorted(
            entries,
            key=lambda e: (e.get(FilesColumns.TITLE.value) or "").lower(),
        )

    if sort_mode is SetSortMode.USE_COUNT:
        return sorted(
            entries,
            key=lambda e: (
                -int(e.get(FilesColumns.USE_COUNT.value) or 0),
                (e.get(FilesColumns.TITLE.value) or "").lower(),
            ),
        )

    return list(entries)


def get_kind_of_file_and_validate(file_name: str) -> str:
    """Return ``\"words\"`` or ``\"definitions\"`` from a set file name.

    Args:
        file_name: Path or basename ending in ``_words.csv`` or
            ``_definitions.csv``.

    Returns:
        ``\"words\"`` or ``\"definitions\"``.

    Raises:
        Exception: If the name does not use a supported suffix.
    """
    if file_name.endswith("_words.csv"):
        return "words"
    elif file_name.endswith("_definitions.csv"):
        return "definitions"
    else:
        raise Exception("The file_name must end with _words.csv or _definitions.csv.")


def save_set(data: pd.DataFrame, file_name: str, *, prune_tts: bool = False) -> None:
    """Write a set DataFrame to the CSV directory, keeping the index column.

    Args:
        data: Set table to persist.
        file_name: Set basename or path resolved by ``FilePathManager``.
        prune_tts: When ``True``, drop cached MP3s for phrases that no longer
            appear in any set. Use after editing or importing content, not
            after progress-only saves.
    """
    full_path = FilePathManager.get_csv_path(file_name)
    data.to_csv(full_path, index=True)
    if prune_tts:
        from learning_app.tts.service import garbage_collect_tts_cache

        garbage_collect_tts_cache()


def load_set(file_name: str) -> pd.DataFrame:
    """Load a set CSV with the first column as the DataFrame index.

    Args:
        file_name: Set basename or path resolved by ``FilePathManager``.

    Returns:
        Loaded set table.
    """
    full_path = FilePathManager.get_csv_path(file_name)
    return pd.read_csv(full_path, index_col=0)


def set_file_exists(file_name: str) -> bool:
    """Return whether the set CSV exists on disk.

    Args:
        file_name: Set basename or path resolved by ``FilePathManager``.
    """
    return os.path.exists(FilePathManager.get_csv_path(file_name))


def sanitize_file_name(file_name: str, kind: str) -> str:
    """Build a safe set basename with the given kind suffix.

    Non-alphanumeric characters are stripped before ``_{kind}.csv`` is
    appended.

    Args:
        file_name: Raw title or stem supplied by the user.
        kind: ``\"words\"`` or ``\"definitions\"``.

    Returns:
        Basename such as ``Animals_words.csv``.
    """
    file_name = "".join([c for c in file_name if c.isalnum()]).rstrip()
    file_name = f"{file_name}_{kind}.csv"
    return file_name


def get_file_names_and_titles(sort_mode: SetSortMode = SetSortMode.LAST_USED) -> list[dict]:
    """Return catalog entries with absolute CSV paths, titles, and metadata.

    Creates an empty ``files.csv`` when the catalog is missing and migrates
    older catalogs that lack creation/usage columns.

    Args:
        sort_mode: Ordering applied before returning entries.

    Returns:
        List of dicts with ``file_name``, ``title``, ``subtitle``,
        ``created_at``, ``last_used``, and ``use_count`` keys.
        ``file_name`` values are absolute paths.
    """
    files_data_path = FilePathManager.get_files_data_path()

    if not os.path.exists(files_data_path):
        generate_empty_files_data()

    df_files = ensure_files_catalog_columns(pd.read_csv(files_data_path))
    df_files[FilesColumns.SUBTITLE.value] = df_files[FilesColumns.SUBTITLE.value].apply(
        lambda x: "" if pd.isna(x) else x
    )

    result = []
    for _, row in df_files.iterrows():
        entry = {
            FilesColumns.FILE_NAME.value: FilePathManager.get_csv_path(row[FilesColumns.FILE_NAME.value]),
            FilesColumns.TITLE.value: row[FilesColumns.TITLE.value],
            FilesColumns.SUBTITLE.value: row[FilesColumns.SUBTITLE.value],
            FilesColumns.CREATED_AT.value: (
                "" if pd.isna(row[FilesColumns.CREATED_AT.value]) else str(row[FilesColumns.CREATED_AT.value])
            ),
            FilesColumns.LAST_USED.value: (
                "" if pd.isna(row[FilesColumns.LAST_USED.value]) else str(row[FilesColumns.LAST_USED.value])
            ),
            FilesColumns.USE_COUNT.value: int(row[FilesColumns.USE_COUNT.value] or 0),
        }
        result.append(entry)
    return sort_catalog_entries(result, sort_mode)


def get_file_names() -> list:
    """Return basenames listed in ``files.csv``.

    Creates an empty catalog when missing.

    Returns:
        List of set file basenames.
    """
    files_data_path = FilePathManager.get_files_data_path()

    if not os.path.exists(files_data_path):
        generate_empty_files_data()

    df_files = ensure_files_catalog_columns(pd.read_csv(files_data_path))
    return df_files[FilesColumns.FILE_NAME.value].tolist()


def generate_empty_files_data() -> None:
    """Create an empty ``files.csv`` catalog with the expected columns."""
    files_data_path = FilePathManager.get_files_data_path()

    df = pd.DataFrame(columns=_CATALOG_COLUMN_ORDER)
    df.to_csv(files_data_path, index=False)


def set_default_progress(file_name: str) -> None:
    """Reset learning statistics on an existing set without removing content.

    Args:
        file_name: Set basename or path to reload and save.
    """
    data = load_set(file_name)
    default_values = {
        StatsColumns.CORRECT_ANSWERS.value: 0,
        StatsColumns.GOOD_ANSWER.value: False,
        StatsColumns.GOOD_ANSWERS_IN_A_ROW.value: False,
        StatsColumns.WORD_TO_LEARN.value: False,
    }
    for col in default_values.keys():
        data[col] = default_values[col]

    save_set(data, file_name)


def get_set_learn_progress(file_name: str) -> tuple[int, int]:
    """Return weighted learn progress without starting a learn session.

    Matches the learn-menu bar: Known rows count as ``1``, rows still in the
    learning mix (``Learned`` / queued) count as ``0.25``, and unverified
    ``0/0/0`` rows count as ``0``. Values are stored in quarters so callers
    can use ``units / max_units`` the same way ``WordListMenu`` does
    (``known * 4 + learning * 1`` over ``total * 4``).

    Missing files or unreadable tables return ``(0, 0)``.

    Args:
        file_name: Set basename or path resolved by ``FilePathManager``.

    Returns:
        ``(units, max_units)`` in quarter-word weights.
    """
    try:
        data = load_set(file_name)
    except (OSError, pd.errors.EmptyDataError, pd.errors.ParserError, ValueError):
        return 0, 0

    total = len(data)
    required = (
        StatsColumns.GOOD_ANSWER.value,
        StatsColumns.GOOD_ANSWERS_IN_A_ROW.value,
        StatsColumns.WORD_TO_LEARN.value,
    )
    if total == 0 or not all(col in data.columns for col in required):
        return 0, int(total) * 4

    known_mask = (
        (data[StatsColumns.GOOD_ANSWER.value] == True)
        & (data[StatsColumns.GOOD_ANSWERS_IN_A_ROW.value] == True)
        & (data[StatsColumns.WORD_TO_LEARN.value] == False)
    )
    unverified_mask = (
        (data[StatsColumns.GOOD_ANSWER.value] == False)
        & (data[StatsColumns.GOOD_ANSWERS_IN_A_ROW.value] == False)
        & (data[StatsColumns.WORD_TO_LEARN.value] == False)
    )
    known = int(known_mask.sum())
    learning = total - known - int(unverified_mask.sum())
    return known * 4 + learning, total * 4


def delate_set(file_name: str, file_not_exist: bool = False) -> None:
    """Remove a set from the catalog and optionally delete its CSV file.

    Args:
        file_name: Set basename or path whose basename is matched in the
            catalog.
        file_not_exist: When ``True``, only the catalog row is removed and the
            CSV file is left untouched even if present.
    """
    files_data_path = FilePathManager.get_files_data_path()

    if not os.path.exists(files_data_path):
        generate_empty_files_data()

    df_files = ensure_files_catalog_columns(pd.read_csv(files_data_path))
    df_files = df_files[df_files[FilesColumns.FILE_NAME.value] != os.path.basename(file_name)]
    df_files.to_csv(files_data_path, index=False)

    full_path = FilePathManager.get_csv_path(file_name)
    if not file_not_exist and os.path.exists(full_path):
        os.remove(full_path)

    from learning_app.tts.service import garbage_collect_tts_cache

    garbage_collect_tts_cache()


def add_new_file(file_name: str, title: str, subtitle: str = "") -> None:
    """Append a row to ``files.csv`` for an existing set file.

    Args:
        file_name: Set basename or path; only the basename is stored.
        title: Display title for tiles.
        subtitle: Optional secondary text.
    """
    files_data_path = FilePathManager.get_files_data_path()

    if not os.path.exists(files_data_path):
        generate_empty_files_data()

    df_files = ensure_files_catalog_columns(pd.read_csv(files_data_path))
    new_row = {
        FilesColumns.FILE_NAME.value: os.path.basename(file_name),
        FilesColumns.TITLE.value: title,
        FilesColumns.SUBTITLE.value: subtitle,
        FilesColumns.CREATED_AT.value: _utc_now_iso(),
        FilesColumns.LAST_USED.value: "",
        FilesColumns.USE_COUNT.value: 0,
    }
    df_files = pd.concat([df_files, pd.DataFrame([new_row])], ignore_index=True)
    df_files.to_csv(files_data_path, index=False)


def update_set_metadata(file_name: str, title: str, subtitle: str = "") -> None:
    """Update display title and subtitle for a catalog entry in ``files.csv``.

    Does not rename the set file; only the tile metadata changes.

    Args:
        file_name: Set basename or path whose basename is matched in the catalog.
        title: New display title.
        subtitle: New secondary text (may be empty).
    """
    files_data_path = FilePathManager.get_files_data_path()

    if not os.path.exists(files_data_path):
        return

    df_files = ensure_files_catalog_columns(pd.read_csv(files_data_path))
    basename = os.path.basename(file_name)
    mask = df_files[FilesColumns.FILE_NAME.value] == basename
    if not mask.any():
        return

    df_files.loc[mask, FilesColumns.TITLE.value] = title
    df_files.loc[mask, FilesColumns.SUBTITLE.value] = subtitle
    df_files.to_csv(files_data_path, index=False)


def record_set_use(file_name: str) -> None:
    """Increment use count and set last-used time for a catalog entry.

    Called when the user opens a set's learn screen.

    Args:
        file_name: Set basename or path whose basename is matched in the catalog.
    """
    files_data_path = FilePathManager.get_files_data_path()

    if not os.path.exists(files_data_path):
        return

    df_files = ensure_files_catalog_columns(pd.read_csv(files_data_path))
    basename = os.path.basename(file_name)
    mask = df_files[FilesColumns.FILE_NAME.value] == basename
    if not mask.any():
        return

    df_files.loc[mask, FilesColumns.LAST_USED.value] = _utc_now_iso()
    df_files.loc[mask, FilesColumns.USE_COUNT.value] = (
        pd.to_numeric(df_files.loc[mask, FilesColumns.USE_COUNT.value], errors="coerce").fillna(0).astype(int) + 1
    )
    df_files.to_csv(files_data_path, index=False)


def create_empty_set(kind: str) -> pd.DataFrame:
    """Return an empty typed DataFrame for a new words or definitions set.

    Args:
        kind: ``\"words\"`` or ``\"definitions\"``.

    Returns:
        Empty DataFrame with content and statistics columns.

    Raises:
        AssertionError: If ``kind`` is not supported.
    """
    assert kind in ["words", "definitions"], "The kind must be 'words' or 'definitions'."
    column_types_words = {
        PartsOfSpeech.VERB.value: str,
        PartsOfSpeech.PERSON.value: str,
        PartsOfSpeech.THING.value: str,
        PartsOfSpeech.ADJECTIVE.value: str,
        PartsOfSpeech.ADVERB.value: str,
        StatsColumns.CORRECT_ANSWERS.value: int,
        StatsColumns.GOOD_ANSWERS_IN_A_ROW.value: bool,
        StatsColumns.GOOD_ANSWER.value: bool,
        StatsColumns.WORD_TO_LEARN.value: bool,
    }

    column_types_definitions = {
        WordDefinitions.DEFINITION.value: str,
        WordDefinitions.WORD.value: str,
        StatsColumns.CORRECT_ANSWERS.value: int,
        StatsColumns.GOOD_ANSWERS_IN_A_ROW.value: bool,
        StatsColumns.GOOD_ANSWER.value: bool,
        StatsColumns.WORD_TO_LEARN.value: bool,
    }

    if kind == "words":
        df = pd.DataFrame({
            PartsOfSpeech.VERB.value: [],
            PartsOfSpeech.PERSON.value: [],
            PartsOfSpeech.THING.value: [],
            PartsOfSpeech.ADJECTIVE.value: [],
            PartsOfSpeech.ADVERB.value: [],
            StatsColumns.CORRECT_ANSWERS.value: [],
            StatsColumns.GOOD_ANSWERS_IN_A_ROW.value: [],
            StatsColumns.GOOD_ANSWER.value: [],
            StatsColumns.WORD_TO_LEARN.value: [],
        }).astype(column_types_words)
        return df

    elif kind == "definitions":
        df = pd.DataFrame({
            WordDefinitions.DEFINITION.value: [],
            WordDefinitions.WORD.value: [],
            StatsColumns.CORRECT_ANSWERS.value: [],
            StatsColumns.GOOD_ANSWERS_IN_A_ROW.value: [],
            StatsColumns.GOOD_ANSWER.value: [],
            StatsColumns.WORD_TO_LEARN.value: [],
        }).astype(column_types_definitions)
        return df


class AppData:
    """In-memory learning session over one set CSV.

    Loads the set, draws practice index groups from statistics columns, and
    saves progress after each answer. Catalog and empty-set helpers remain
    module-level functions outside this class.

    Attributes:
        last_group_of_indexes: Class-level list of indexes from the last drawn
            group when ``draw_index_group(save_indexes_in_class_art=True)``.
        words: Loaded set DataFrame.
        file_name: Set path or basename used for load/save.
        kind: ``\"words\"`` or ``\"definitions\"``.
    """

    last_group_of_indexes = []

    def __init__(self, file_name: str):
        """Load ``file_name`` and prepare the first practice group.

        Args:
            file_name: Set basename or path ending in ``_words.csv`` or
                ``_definitions.csv``.

        Raises:
            Exception: If the kind suffix is invalid.
            AssertionError: If required content or statistics columns are
                missing.
        """
        self.words = load_set(file_name)
        self.file_name = file_name
        self.current_group_of_indexes = []
        self.place_of_group_index = 0
        self.len_of_group = 0
        self.draw_index_group()
        self.current_word_index = 0
        self.current_word_row = self.words.loc[self.current_word_index]

        self.kind = get_kind_of_file_and_validate(file_name)

        self.stats_columns = [
            StatsColumns.CORRECT_ANSWERS.value,
            StatsColumns.GOOD_ANSWER.value,
            StatsColumns.GOOD_ANSWERS_IN_A_ROW.value,
            StatsColumns.WORD_TO_LEARN.value,
        ]

        if self.kind not in ["words", "definitions"]:
            raise Exception("The kind must be 'words' or 'definitions'.")

        if self.kind == "words":
            assert PartsOfSpeech.VERB.value in self.words.columns and \
                   PartsOfSpeech.PERSON.value in self.words.columns and \
                   PartsOfSpeech.THING.value in self.words.columns and \
                   PartsOfSpeech.ADJECTIVE.value in self.words.columns and \
                   PartsOfSpeech.ADVERB.value in self.words.columns \
                   , "The columns must be: verb, person, thing, adjective, adverb."

        elif self.kind == "definitions":
            assert WordDefinitions.DEFINITION.value in self.words.columns and \
                   WordDefinitions.WORD.value in self.words.columns \
                   , "The columns must be: definition, word."

        for col in self.stats_columns:
            assert col in self.words.columns, f"The column {col} is missing."

    def draw_index_group(self, save_indexes_in_class_art: bool = False) -> int:
        """Draw up to ten row indexes for the next practice group.

        Prefers ``word_to_learn`` rows, then fills from other statistics
        combinations ordered by ``correct_answers``.

        Args:
            save_indexes_in_class_art: When ``True``, store the drawn indexes
                on ``AppData.last_group_of_indexes``.

        Returns:
            Number of indexes in the new group, or ``0`` when none are
            available.
        """
        indexes_to_draw = self.words[(self.words[StatsColumns.GOOD_ANSWER.value] == False) &
                                     (self.words[StatsColumns.GOOD_ANSWERS_IN_A_ROW.value] == False) &
                                     (self.words[StatsColumns.WORD_TO_LEARN.value] == True)].index

        for i in range(2):
            if len(indexes_to_draw) >= 10:
                break
            elif i == 0:  # Add to indexes_to_draw indexes where:  0/0/0
                qty_to_add = 10 - len(indexes_to_draw)
                self.words.sort_values(by=StatsColumns.CORRECT_ANSWERS.value, inplace=True)
                indexes_to_draw = indexes_to_draw.union(self.words[
                    (self.words[StatsColumns.GOOD_ANSWER.value] == False) &
                    (self.words[StatsColumns.GOOD_ANSWERS_IN_A_ROW.value] == False) &
                    (self.words[StatsColumns.WORD_TO_LEARN.value] == False)].index[:qty_to_add])

            elif i == 1:  # Add to indexes_to_draw indexes where:  1/0/0 or 1/0/1 or 1/1/1
                qty_to_add = 10 - len(indexes_to_draw)
                self.words.sort_values(by=StatsColumns.CORRECT_ANSWERS.value, inplace=True)
                indexes_to_draw = indexes_to_draw.union(self.words[
                    ((self.words[StatsColumns.GOOD_ANSWER.value] == True) &
                     (self.words[StatsColumns.GOOD_ANSWERS_IN_A_ROW.value] == False)) |
                    ((self.words[StatsColumns.GOOD_ANSWER.value] == True) &
                     (self.words[StatsColumns.WORD_TO_LEARN.value] == True))].index[:qty_to_add])

        number_of_indexes = len(indexes_to_draw)
        if number_of_indexes > 10:
            number_of_indexes = 10
        elif number_of_indexes == 0:
            return 0

        indexes = rd.sample(indexes_to_draw.tolist(), number_of_indexes)
        self.current_group_of_indexes = indexes
        self.place_of_group_index = 0
        self.len_of_group = number_of_indexes

        if save_indexes_in_class_art:
            self.__class__.last_group_of_indexes = indexes

        return number_of_indexes

    def __get_next_index(self):
        ret = self.current_group_of_indexes[self.place_of_group_index]
        self.place_of_group_index += 1

        if self.place_of_group_index == self.len_of_group:
            self.current_group_of_indexes = []
            self.place_of_group_index = 0
            self.len_of_group = 0

        return ret

    def draw_new_row(self) -> None:
        """Advance to the next index in the current practice group."""
        self.current_word_index = self.__get_next_index()
        self.current_word_row = self.words.loc[self.current_word_index]

    def get_current_row(self) -> pd.Series:
        """Return the current content row without statistics columns."""
        return self.current_word_row.dropna().drop(self.stats_columns)

    def get_current_words_list(self) -> list:
        """Return the current content row values as a list."""
        return self.get_current_row().tolist()

    def colnames_in_WordFields(self) -> list:
        """Return content column names for the current row (no stats)."""
        return [col for col in self.current_word_row.index if col not in self.stats_columns]

    def good_answer_at_current_row(self) -> None:
        """Record a correct answer, update statistics flags, and save the set."""
        self.words.at[self.current_word_index, StatsColumns.CORRECT_ANSWERS.value] += 1

        special_case = self.words.at[self.current_word_index, StatsColumns.GOOD_ANSWER.value] and \
            self.words.at[self.current_word_index, StatsColumns.GOOD_ANSWERS_IN_A_ROW.value] and \
            self.words.at[self.current_word_index, StatsColumns.WORD_TO_LEARN.value]

        spacial_case2 = self.words.at[self.current_word_index, StatsColumns.GOOD_ANSWER.value] and \
            (not self.words.at[self.current_word_index, StatsColumns.GOOD_ANSWERS_IN_A_ROW.value]) and \
            self.words.at[self.current_word_index, StatsColumns.WORD_TO_LEARN.value]

        previous_good_answer = self.words.at[self.current_word_index, StatsColumns.GOOD_ANSWER.value]
        if previous_good_answer:
            self.words.at[self.current_word_index, StatsColumns.GOOD_ANSWERS_IN_A_ROW.value] = True

        self.words.at[self.current_word_index, StatsColumns.GOOD_ANSWER.value] = True

        if special_case:
            self.words.at[self.current_word_index, StatsColumns.WORD_TO_LEARN.value] = False
        elif spacial_case2:
            self.words.at[self.current_word_index, StatsColumns.GOOD_ANSWERS_IN_A_ROW.value] = True
            self.words.at[self.current_word_index, StatsColumns.WORD_TO_LEARN.value] = False

        save_set(self.words, self.file_name)

    def bad_answer_at_current_row(self) -> None:
        """Record an incorrect answer, mark the row to learn, and save the set."""
        self.words.at[self.current_word_index, StatsColumns.GOOD_ANSWER.value] = False
        self.words.at[self.current_word_index, StatsColumns.GOOD_ANSWERS_IN_A_ROW.value] = False
        self.words.at[self.current_word_index, StatsColumns.WORD_TO_LEARN.value] = True
        save_set(self.words, self.file_name)

    def it_is_not_last_index_of_group(self) -> bool:
        """Return whether the current group still has unread indexes."""
        return self.place_of_group_index != self.len_of_group

    def number_of_known_words(self) -> int:
        """Count rows in the fully learned statistics state."""
        temp_words = self.words[(self.words[StatsColumns.GOOD_ANSWER.value] == True) &
                                (self.words[StatsColumns.GOOD_ANSWERS_IN_A_ROW.value] == True) &
                                (self.words[StatsColumns.WORD_TO_LEARN.value] == False)]

        if temp_words.empty:
            return 0
        else:
            return len(temp_words)

    def number_of_learning_words(self) -> int:
        """Count rows that are actively in the learning queue."""
        temp_words = self.words[(self.words[StatsColumns.GOOD_ANSWER.value] == False) &
                                (self.words[StatsColumns.GOOD_ANSWERS_IN_A_ROW.value] == False) &
                                (self.words[StatsColumns.WORD_TO_LEARN.value] == False)]

        subtract = 0

        if not temp_words.empty:
            subtract = len(temp_words)

        return len(self.words) - self.number_of_known_words() - subtract

    def number_of_all_words(self) -> int:
        """Return the total number of rows in the loaded set."""
        return len(self.words)

    def are_all_words_learned(self) -> bool:
        """Return whether every row is in the fully learned state."""
        if self.number_of_known_words() == self.number_of_all_words():
            return True
        else:
            return False

    def refresh(self) -> None:
        """Reload the set CSV from disk into ``words``."""
        self.words = load_set(self.file_name)

    @classmethod
    def was_this_index_drawn(cls, index: int) -> bool:
        """Return whether ``index`` was in the last saved practice group.

        Args:
            index: Row index to look up in ``last_group_of_indexes``.
        """
        return index in cls.last_group_of_indexes

    @classmethod
    def delete_last_group_of_indexes(cls) -> None:
        """Clear ``last_group_of_indexes``."""
        cls.last_group_of_indexes = []

    def colnames_with_nan(self) -> list:
        """Return content column names that are empty on the current words row.

        Raises:
            Exception: If the loaded set is not a words set.
        """
        if self.kind != "words":
            raise Exception("This method is only for the 'words' kind.")

        return self.current_word_row[self.current_word_row.isnull()].index.tolist()

    @staticmethod
    def create_data_file_words(file_name: str, title: str, subtitle: str = "") -> None:
        """Create an empty set CSV and register it in the catalog.

        Despite the historical name, ``file_name`` may be a words or
        definitions set; the kind is taken from the suffix.

        Args:
            file_name: Target basename ending in ``_words.csv`` or
                ``_definitions.csv``.
            title: Catalog title.
            subtitle: Optional catalog subtitle.
        """
        files_data_path = FilePathManager.get_files_data_path()
        if not os.path.exists(files_data_path):
            generate_empty_files_data()

        kind = get_kind_of_file_and_validate(file_name)

        df = create_empty_set(kind)
        save_set(df, file_name)

        add_new_file(file_name, title, subtitle)
