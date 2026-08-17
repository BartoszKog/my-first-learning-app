"""Import validation, catalog repair, and CSV save helpers for learning sets.

``CSVProcessor`` inspects picked files, reports ``Errors`` / ``Warnings``, and
writes normalized set CSVs plus ``files.csv`` catalog rows. Prefer the public
static methods from Import/Export UI code; private ``__`` helpers stay
internal.
"""

import csv
import os
import warnings as py_warnings

import pandas as pd

from learning_app.data.app_data import add_new_file, save_set
from learning_app.data.constants import Errors, FilesColumns, MAX_ROWS, PartsOfSpeech, StatsColumns, Warnings, WordDefinitions
from learning_app.data.demo_sets import allocate_unique_set_basename
from learning_app.data.file_path_manager import FilePathManager

_SET_SUFFIXES = ("_words.csv", "_definitions.csv")
_REQUIRED_CATALOG_COLUMNS = (
    FilesColumns.FILE_NAME.value,
    FilesColumns.TITLE.value,
    FilesColumns.SUBTITLE.value,
)


def _title_from_set_basename(file_name: str) -> str:
    name = os.path.basename(str(file_name))
    for suffix in _SET_SUFFIXES:
        if name.endswith(suffix):
            stem = name[: -len(suffix)]
            return stem.capitalize() if stem else name
    return name


def _catalog_from_set_files_on_disk() -> pd.DataFrame:
    csv_dir = FilePathManager.get_csv_dir()
    rows = []
    if os.path.isdir(csv_dir):
        for name in sorted(os.listdir(csv_dir)):
            if name.endswith(_SET_SUFFIXES):
                rows.append({
                    FilesColumns.FILE_NAME.value: name,
                    FilesColumns.TITLE.value: _title_from_set_basename(name),
                    FilesColumns.SUBTITLE.value: "",
                })
    return pd.DataFrame(rows, columns=list(_REQUIRED_CATALOG_COLUMNS))


def _fill_missing_required_catalog_columns(files_data: pd.DataFrame) -> tuple[pd.DataFrame, list[str]]:
    """Add required catalog columns without wiping existing rows.

    When ``file_name`` is missing, rows cannot be matched to set files, so the
    catalog is rebuilt from ``*_words.csv`` / ``*_definitions.csv`` on disk.
    """
    actions: list[str] = []
    missing = [col for col in _REQUIRED_CATALOG_COLUMNS if col not in files_data.columns]
    if not missing:
        return files_data, actions

    if FilesColumns.FILE_NAME.value not in files_data.columns:
        rebuilt = _catalog_from_set_files_on_disk()
        actions.append(
            "Rebuilt catalog from set files on disk because the file_name column was missing"
        )
        return rebuilt, actions

    files_data = files_data.copy()
    if FilesColumns.TITLE.value not in files_data.columns:
        files_data[FilesColumns.TITLE.value] = files_data[FilesColumns.FILE_NAME.value].map(
            lambda value: _title_from_set_basename(value) if pd.notna(value) else ""
        )
        actions.append("Added missing title column from file names")
    if FilesColumns.SUBTITLE.value not in files_data.columns:
        files_data[FilesColumns.SUBTITLE.value] = ""
        actions.append("Added missing subtitle column")
    return files_data, actions


def _recover_catalog_csv(path: str) -> tuple[pd.DataFrame | None, list[str]]:
    """Rebuild a catalog DataFrame from a CSV pandas refused to parse.

    Extra fields (for example a stray comma) are trimmed to the header width;
    short rows are padded. Returns ``None`` when the file cannot be read as
    text or has no usable header.
    """
    try:
        with open(path, newline="", encoding="utf-8-sig") as handle:
            rows = list(csv.reader(handle))
    except (OSError, UnicodeError, csv.Error):
        return None, []

    rows = [row for row in rows if any(str(cell).strip() for cell in row)]
    if not rows:
        return None, []

    header = [cell.strip() for cell in rows[0]]
    while header and header[-1] == "":
        header.pop()
    if not header:
        return None, []

    width = len(header)
    truncated = 0
    padded = 0
    data = []
    for row in rows[1:]:
        if len(row) > width:
            row = row[:width]
            truncated += 1
        elif len(row) < width:
            row = row + [""] * (width - len(row))
            padded += 1
        data.append(row)

    actions = ["Recovered catalog rows from a CSV that pandas could not parse"]
    if truncated:
        actions.append(f"Trimmed extra fields on {truncated} row(s)")
    if padded:
        actions.append(f"Padded missing fields on {padded} row(s)")
    return pd.DataFrame(data, columns=header), actions


def _is_set_basename(name: object) -> bool:
    return str(name).endswith(_SET_SUFFIXES)


def _catalog_file_names_are_valid(files_data: pd.DataFrame | None) -> bool:
    if files_data is None or FilesColumns.FILE_NAME.value not in files_data.columns:
        return False
    if files_data.empty:
        return True
    return bool(files_data[FilesColumns.FILE_NAME.value].map(_is_set_basename).all())


class CSVProcessor:
    """Validate and import learning-set CSVs; validate or repair ``files.csv``."""

    @staticmethod
    def __add_statistics_columns(df: pd.DataFrame) -> pd.DataFrame:
        # Add statistics columns to the DataFrame
        df[StatsColumns.CORRECT_ANSWERS.value] = 0
        df[StatsColumns.GOOD_ANSWERS_IN_A_ROW.value] = False
        df[StatsColumns.GOOD_ANSWER.value] = False
        df[StatsColumns.WORD_TO_LEARN.value] = False
        return df

    @staticmethod
    def __reset_statistics_columns(df: pd.DataFrame) -> pd.DataFrame:
        # Only drop columns that actually exist in the dataframe
        stat_cols_to_drop = [col.value for col in StatsColumns if col.value in df.columns]
        if stat_cols_to_drop:
            df = df.drop(columns=stat_cols_to_drop)
        # Add all statistics columns (whether they existed before or not)
        df = CSVProcessor.__add_statistics_columns(df)
        return df

    @staticmethod
    def __sanitize_file_name(file_name: str, suffix: str) -> str:
        # remove suffix from the file name
        file_name = file_name[:-len(suffix)] if suffix else file_name
        file_name = "".join([char for char in file_name if char.isalnum()])
        # add suffix to the file name
        file_name += suffix
        return file_name

    @staticmethod
    def __create_appropriate_file_name(imported_file_name: str) -> str:
        # raise exception if imported_file_name is None
        if imported_file_name is None:
            raise ValueError("imported_file_name cannot be None")
        # raise exception if imported_file_name does not end with some suffix
        suffixes = ["_words.csv", "_definitions.csv"]
        if not any(imported_file_name.endswith(suffix) for suffix in suffixes):
            raise ValueError(f"imported_file_name {imported_file_name} does not end with any of the expected suffixes")

        chosen_suffix = next((suffix for suffix in suffixes if imported_file_name.endswith(suffix)), None)
        base_name = CSVProcessor.__sanitize_file_name(imported_file_name, chosen_suffix)
        return allocate_unique_set_basename(base_name)

    @staticmethod
    def __make_index_from_zero_increasing_by_one(df: pd.DataFrame) -> pd.DataFrame:
        # Remove any 'Unnamed: 0' columns if they exist
        if "Unnamed: 0" in df.columns:
            df = df.drop(columns=["Unnamed: 0"])
        # Reset index
        df.index = range(len(df))
        return df

    @staticmethod
    def __read_csv_file(file_path: str, index_present: bool = True) -> pd.DataFrame:
        try:
            if index_present:
                df = pd.read_csv(file_path, index_col=0)
            else:
                df = pd.read_csv(file_path)
        except Exception:
            # If that fails, load without setting an index
            df = pd.read_csv(file_path)

        # Remove any 'Unnamed: 0' columns if they exist
        if "Unnamed: 0" in df.columns:
            df = df.drop(columns=["Unnamed: 0"])

        return df

    @staticmethod
    def __indexes_of_rows_with_insufficient_non_empty_values(df: pd.DataFrame, data_type: str) -> list:
        # raising exception if data_type is not implemented
        if data_type not in ["words", "definitions"]:
            raise ValueError(f"data_type {data_type} is not implemented")
        # get the indexes of rows with insufficient non-empty values
        if data_type == "words":
            typical_columns = [col.value for col in PartsOfSpeech]
        else:  # data_type == "definitions"
            typical_columns = [col.value for col in WordDefinitions]

        indexes = df[typical_columns].isnull().sum(axis=1) >= (len(typical_columns) - 1)
        return indexes.index[indexes].tolist()

    @staticmethod
    def __keep_necessary_columns(df: pd.DataFrame, data_type: str) -> pd.DataFrame:
        if data_type == "words":
            cols_to_keep = [col.value for col in PartsOfSpeech if col.value in df.columns]
            return df[cols_to_keep]
        elif data_type == "definitions":
            cols_to_keep = [col.value for col in WordDefinitions if col.value in df.columns]
            return df[cols_to_keep]
        else:
            raise ValueError(f"data_type {data_type} is not implemented")

    @staticmethod
    def save_set_with_no_specific_actions(
        file_path: str,
        file_name: str,
        title: str,
        subtitle: str,
        has_statistics: bool,
        keep_statistics: bool = False,
    ) -> None:
        """Import a CSV that needs no warning-driven repair.

        Adds or resets statistics columns, normalizes the index, allocates a
        unique basename, registers the catalog row, and saves the set.

        Args:
            file_path: Absolute path of the picked source file.
            file_name: Original basename used to build the stored name.
            title: Catalog title.
            subtitle: Catalog subtitle.
            has_statistics: Whether the source already has usable stats
                columns.
            keep_statistics: When ``has_statistics`` is ``True``, keep existing
                progress if ``True``; otherwise reset statistics.
        """
        if file_path is None or file_name is None:
            raise ValueError("file_path and file_name cannot be None")

        # Read directly from the provided path
        df = CSVProcessor.__read_csv_file(file_path)

        if not has_statistics:
            df = CSVProcessor.__add_statistics_columns(df)
        elif not keep_statistics:
            df = CSVProcessor.__reset_statistics_columns(df)

        # correct the index
        df = CSVProcessor.__make_index_from_zero_increasing_by_one(df)

        file_name = CSVProcessor.__create_appropriate_file_name(file_name)
        add_new_file(file_name, title, subtitle)
        save_set(df, file_name, prune_tts=True)

    @staticmethod
    def save_set_with_specific_actions(
        file_path: str,
        file_name: str,
        title: str,
        subtitle: str,
        data_type: str,
        has_statistics: bool,
        warnings: list,
        keep_statistics: bool = False,
    ) -> str:
        """Import a CSV that requires warning-driven cleanup before save.

        Applies repairs implied by ``warnings`` (index handling, dropping
        sparse rows, discarding broken statistics) and normalizes the stored
        basename suffix from ``data_type``, then registers and saves the set.

        Args:
            file_path: Absolute path of the picked source file.
            file_name: Original basename used to build the stored name.
            title: Catalog title.
            subtitle: Catalog subtitle.
            data_type: ``\"words\"`` or ``\"definitions\"``.
            has_statistics: Whether validation found usable stats columns.
            warnings: Warning strings from ``validate_file``.
            keep_statistics: Keep existing progress when statistics are still
                usable and the user confirms.

        Returns:
            Optional information string for the UI (empty when nothing extra
            must be shown).
        """
        if file_path is None or file_name is None or data_type is None:
            raise ValueError("file_path, file_name and data_type cannot be None")
        if data_type not in ["words", "definitions"]:
            raise ValueError(f"data_type {data_type} is not implemented")

        information_after_processing = ""

        # read the file based on index warning
        index_present = Warnings.FIRST_COLUMN_NOT_INDEX.value not in warnings
        df = CSVProcessor.__read_csv_file(file_path, index_present)

        # sort out rows with empty values in typical columns
        insufficient_non_empty_values_indexes = Warnings.INSUFFICIENT_NON_EMPTY_VALUES.value in warnings
        if insufficient_non_empty_values_indexes:
            indexes = CSVProcessor.__indexes_of_rows_with_insufficient_non_empty_values(df, data_type)
            df = df.drop(indexes)

        # if there are any warnings about statistics, drop the statistics columns
        statistics_warnings = [
            Warnings.COLUMN_NOT_BOOLEAN.value,
            Warnings.COLUMN_NOT_INTEGER.value,
            Warnings.EMPTY_VALUES_STATISTICS.value,
            Warnings.INCONSISTENT_STATISTICS_COMBINATION.value,
            Warnings.NEGATIVE_CORRECT_ANSWERS.value,
        ]

        if any(warning in warnings for warning in statistics_warnings):
            information_after_processing += "Statistics columns have errors, so progress information cannot be added. The set will be added to the application without progress data."
            if has_statistics:
                # Check which statistics columns actually exist before dropping
                stat_cols_to_drop = [col.value for col in StatsColumns if col.value in df.columns]
                if stat_cols_to_drop:
                    df = df.drop(columns=stat_cols_to_drop)
                has_statistics = False

        if not has_statistics:
            df = CSVProcessor.__keep_necessary_columns(df, data_type)
            df = CSVProcessor.__add_statistics_columns(df)
        else:
            if not keep_statistics:
                df = CSVProcessor.__keep_necessary_columns(df, data_type)
                df = CSVProcessor.__reset_statistics_columns(df)
            else:
                # Check which statistics columns actually exist before selecting
                stat_cols = [col.value for col in StatsColumns if col.value in df.columns]
                if len(stat_cols) == len(StatsColumns):
                    statistics_df = df[stat_cols]
                    df = CSVProcessor.__keep_necessary_columns(df, data_type)
                    df = pd.concat([df, statistics_df], axis=1)
                else:
                    # If some statistics columns are missing, reset them
                    df = CSVProcessor.__keep_necessary_columns(df, data_type)
                    df = CSVProcessor.__add_statistics_columns(df)

        # preparing file name (suffix is an internal convention; repair silently)
        expected_suffix = f"_{data_type}.csv"
        if file_name.endswith(expected_suffix):
            file_name = CSVProcessor.__create_appropriate_file_name(file_name)
        else:
            file_name = CSVProcessor.__sanitize_file_name(file_name, "")
            file_name += expected_suffix
            file_name = CSVProcessor.__create_appropriate_file_name(file_name)

        # correct the index
        df = CSVProcessor.__make_index_from_zero_increasing_by_one(df)

        add_new_file(file_name, title, subtitle)
        save_set(df, file_name, prune_tts=True)
        return information_after_processing

    @staticmethod
    def validate_file(file_path: str, original_name: str | None = None) -> dict:
        """Validate a picked learning-set CSV before import.

        Args:
            file_path: Absolute path to the candidate ``.csv`` file
                (may be a temporary path when the picker has no filesystem
                path, e.g. on web).
            original_name: Display/basename from the file picker. Used for
                title suggestion and suffix checks so temporary paths do not
                leak random names into the UI. Defaults to
                ``os.path.basename(file_path)``.

        Returns:
            Dict with ``errors``, ``warnings``, ``is_valid``,
            ``requires_specific_actions``, ``has_statistics``,
            ``name_suggestion``, and ``data_type``.
        """
        errors = []
        warnings = []
        is_valid = True
        requires_specific_actions = False
        has_statistics = False
        name_suggestion = ""
        data_type = ""
        name_source = os.path.basename(original_name) if original_name else os.path.basename(file_path)

        def validate_columns(expected_columns, df_columns, error_message):
            nonlocal requires_specific_actions
            if not expected_columns.issubset(df_columns):
                errors.append(error_message.value)
                return False
            unnecessary_columns = set(df_columns) - expected_columns - {col.value for col in StatsColumns}
            if unnecessary_columns:
                warnings.append(Warnings.UNNECESSARY_COLUMNS.value)
                requires_specific_actions = True
            return True

        def check_missing_data(typical_columns, df):
            nonlocal requires_specific_actions
            if data_type == "words":
                insufficient_non_empty_rows = df[typical_columns].isnull().sum(axis=1) >= (len(typical_columns) - 1)
                if insufficient_non_empty_rows.all():
                    errors.append(Errors.INSUFFICIENT_NON_EMPTY_VALUES_IN_WORDS.value)
                    return False
                elif insufficient_non_empty_rows.any():
                    warnings.append(Warnings.INSUFFICIENT_NON_EMPTY_VALUES.value)
                    requires_specific_actions = True
            elif data_type == "definitions":
                rows_with_empty_values = df[typical_columns].isnull().any(axis=1)
                if rows_with_empty_values.all():
                    errors.append(Errors.EMPTY_VALUES_IN_DEFINITIONS.value)
                    return False
                elif rows_with_empty_values.any():
                    warnings.append(Warnings.INSUFFICIENT_NON_EMPTY_VALUES.value)
                    requires_specific_actions = True
            return True

        # Check if the file is a CSV
        if not file_path.endswith(".csv"):
            errors.append(Errors.NOT_A_CSV.value)
            is_valid = False
        else:
            # Try to load the file with pandas
            try:
                df = pd.read_csv(file_path)
            except FileNotFoundError:
                errors.append(Errors.FILE_NOT_FOUND.value)
                is_valid = False
            except Exception:
                errors.append(Errors.ERROR_LOADING_FILE.value)
                is_valid = False

        # Improved check for if the first column could serve as an index
        if is_valid:
            first_col = df.columns[0]
            # Check if first column appears to be an index (numeric and unique values)
            if not pd.api.types.is_numeric_dtype(df[first_col]) or df[first_col].duplicated().any():
                warnings.append(Warnings.FIRST_COLUMN_NOT_INDEX.value)
                requires_specific_actions = True
            else:
                try:
                    df.set_index(first_col, inplace=True)
                except Exception:
                    warnings.append(Warnings.FIRST_COLUMN_NOT_INDEX.value)
                    requires_specific_actions = True

        # Check if the number of rows exceeds the maximum allowed
        if is_valid and len(df) > MAX_ROWS:
            errors.append(Errors.TOO_MANY_ROWS.value)
            is_valid = False

        if is_valid:
            words_columns = {col.value for col in PartsOfSpeech}
            definitions_columns = {col.value for col in WordDefinitions}

            if words_columns.issubset(df.columns):
                data_type = "words"
                expected_suffix = "_words.csv"
                validate_columns(words_columns, df.columns, Errors.MISSING_COLUMNS_WORDS)
            elif definitions_columns.issubset(df.columns):
                data_type = "definitions"
                expected_suffix = "_definitions.csv"
                validate_columns(definitions_columns, df.columns, Errors.MISSING_COLUMNS_DEFINITIONS)
            else:
                errors.append(Errors.NO_MATCHING_COLUMN_PATTERN.value)
                is_valid = False

            # Suffix is an internal storage convention; mismatch only routes
            # save through the repair path (no user-facing warning).
            if data_type:
                if not name_source.endswith(expected_suffix):
                    requires_specific_actions = True

                # Suggest a title only when the original name already uses the
                # app suffix (avoids temp basenames like tmpXXXX on web).
                for suffix in ["_words.csv", "_definitions.csv"]:
                    if name_source.endswith(suffix):
                        name_suggestion = name_source[: -len(suffix)]
                        break

        # Check for statistics columns
        if is_valid:
            stats_columns = {col.value for col in StatsColumns}
            has_statistics = stats_columns.issubset(df.columns)

            # Validate types of statistics columns
            if has_statistics:
                if not pd.api.types.is_numeric_dtype(df[StatsColumns.CORRECT_ANSWERS.value]):
                    warnings.append(Warnings.COLUMN_NOT_INTEGER.value)
                    has_statistics = False
                    requires_specific_actions = True
                for col in [StatsColumns.GOOD_ANSWER.value, StatsColumns.GOOD_ANSWERS_IN_A_ROW.value, StatsColumns.WORD_TO_LEARN.value]:
                    if not pd.api.types.is_bool_dtype(df[col]):
                        warnings.append(Warnings.COLUMN_NOT_BOOLEAN.value)
                        has_statistics = False
                        requires_specific_actions = True
                        break

        # Check for empty values in typical columns based on data type
        if is_valid and data_type:
            typical_columns = [col.value for col in PartsOfSpeech] if data_type == "words" else [col.value for col in WordDefinitions]
            typical_columns = [col for col in typical_columns if col in df.columns]
            if typical_columns and not check_missing_data(typical_columns, df):
                is_valid = False
                errors.append(
                    Errors.MISSING_COLUMNS_DEFINITIONS.value if data_type == "definitions" else
                    Errors.MISSING_COLUMNS_WORDS.value
                )

        # Check for empty values in statistics columns
        if is_valid and has_statistics:
            stats_cols_present = [col for col in stats_columns if col in df.columns]
            if stats_cols_present and df[stats_cols_present].isnull().values.any():
                warnings.append(Warnings.EMPTY_VALUES_STATISTICS.value)
                requires_specific_actions = True
                has_statistics = False

        # Check for inconsistent combinations of statistics and negative values in correct_answers
        if is_valid and has_statistics:
            # check for inconsistent combinations of statistics
            inconsistent_stats_mask = (
                (df[StatsColumns.GOOD_ANSWERS_IN_A_ROW.value] == True) &
                (df[StatsColumns.GOOD_ANSWER.value] == False)
            )

            if inconsistent_stats_mask.any():
                warnings.append(Warnings.INCONSISTENT_STATISTICS_COMBINATION.value)
                requires_specific_actions = True

            # check for invalid numerical values
            if (df[StatsColumns.CORRECT_ANSWERS.value] < 0).any():
                warnings.append(Warnings.NEGATIVE_CORRECT_ANSWERS.value)
                requires_specific_actions = True

        # Remove duplicate warnings
        warnings = list(set(warnings))

        return {
            "errors": errors,
            "warnings": warnings,
            "is_valid": is_valid,
            "requires_specific_actions": requires_specific_actions,
            "has_statistics": has_statistics,
            "name_suggestion": name_suggestion,
            "data_type": data_type,
        }

    @staticmethod
    def validate_files_csv() -> dict:
        """Validate the set catalog ``files.csv``.

        A missing catalog is treated as valid because helpers create it later.
        Repair does not recreate a missing ``files.csv``; that stays with
        catalog readers such as ``get_file_names_and_titles``.
        Missing set files on disk produce warnings; structural problems produce
        errors.

        Returns:
            Dict with ``errors``, ``warnings``, ``is_valid``, and
            ``files_data`` (loaded frame or ``None``).
        """
        errors = []
        warnings = []
        is_valid = True
        files_data = None

        # Check if files.csv exists
        files_data_path = FilePathManager.get_files_data_path()
        if not os.path.exists(files_data_path):
            # If the file doesn't exist, it's ok, since it will be created later in get_file_names_and_titles
            is_valid = True
            return {
                "errors": errors,
                "warnings": warnings,
                "is_valid": is_valid,
                "files_data": None,
            }

        # Try to load the file with pandas
        try:
            with py_warnings.catch_warnings():
                py_warnings.simplefilter("ignore", pd.errors.ParserWarning)
                files_data = pd.read_csv(files_data_path, index_col=False)
        except Exception as e:
            errors.append(f"Error loading files.csv: {str(e)}")
            is_valid = False
            return {
                "errors": errors,
                "warnings": warnings,
                "is_valid": is_valid,
                "files_data": None,
            }

        # Check required columns
        required_columns = [FilesColumns.FILE_NAME.value, FilesColumns.TITLE.value, FilesColumns.SUBTITLE.value]
        missing_columns = [col for col in required_columns if col not in files_data.columns]
        if missing_columns:
            errors.append(f"Missing required columns in files.csv: {', '.join(missing_columns)}")
            is_valid = False

        if not is_valid:
            return {
                "errors": errors,
                "warnings": warnings,
                "is_valid": is_valid,
                "files_data": files_data,
            }

        # Check for empty values in required fields
        if files_data[FilesColumns.FILE_NAME.value].isnull().any():
            errors.append("Found empty file names in files.csv.")
            is_valid = False

        if files_data[FilesColumns.TITLE.value].isnull().any():
            errors.append("Found empty titles in files.csv.")
            is_valid = False

        # Check for duplicate file names
        duplicate_files = files_data[files_data.duplicated(subset=[FilesColumns.FILE_NAME.value], keep=False)]
        if not duplicate_files.empty:
            errors.append(f"Found duplicate file names in files.csv: {', '.join(duplicate_files[FilesColumns.FILE_NAME.value].unique())}")
            is_valid = False

        # Check file name formats
        invalid_file_names = []
        missing_files = []
        for file_name in files_data[FilesColumns.FILE_NAME.value]:
            file_name = str(file_name)
            if not (file_name.endswith("_words.csv") or file_name.endswith("_definitions.csv")):
                invalid_file_names.append(file_name)

            # Check if the file physically exists
            full_path = FilePathManager.get_csv_path(file_name)
            if not os.path.exists(full_path):
                missing_files.append(file_name)

        if invalid_file_names:
            errors.append(f"Invalid file names in files.csv (must end with '_words.csv' or '_definitions.csv'): {', '.join(invalid_file_names)}")
            is_valid = False

        if missing_files:
            warnings.append(f"Files listed in files.csv do not exist on disk: {', '.join(missing_files)}")

        return {
            "errors": errors,
            "warnings": warnings,
            "is_valid": is_valid,
            "files_data": files_data,
        }

    @staticmethod
    def repair_files_csv() -> dict:
        """Attempt to repair ``files.csv`` after a failed validation.

        May recover rows from a CSV pandas cannot parse (extra or missing
        commas), add missing required columns (or rebuild from set files when
        ``file_name`` is absent), drop invalid or duplicate rows, fill empty
        subtitle cells when they are missing, and remove entries for missing
        files. A catalog that cannot be read as text is left unchanged. A
        missing catalog is not created here; catalog readers create it when
        needed.

        Returns:
            Dict with ``repair_actions`` (list of human-readable steps) and
            ``success`` (whether any repair was applied or completed).
        """
        from learning_app.data.app_data import ensure_files_catalog_columns

        validation_result = CSVProcessor.validate_files_csv()
        repair_actions = []

        files_data = validation_result["files_data"]
        recovered_from_parse_error = False
        catalog_path = FilePathManager.get_files_data_path()
        pandas_failed = any("Error loading files.csv" in error for error in validation_result["errors"])

        # csv.reader keeps columns aligned when pandas treats extra commas as an index.
        if os.path.exists(catalog_path):
            recovered, recover_actions = _recover_catalog_csv(catalog_path)
            if recovered is None:
                if pandas_failed or files_data is None:
                    return {
                        "repair_actions": [
                            "Could not load files.csv; left the existing file unchanged",
                        ],
                        "success": False,
                    }
            elif pandas_failed or not _catalog_file_names_are_valid(files_data):
                files_data = recovered
                repair_actions.extend(recover_actions)
                recovered_from_parse_error = True

        # If we have data to work with
        if files_data is not None:
            original_len = len(files_data)

            files_data, column_actions = _fill_missing_required_catalog_columns(files_data)
            repair_actions.extend(column_actions)

            errors = validation_result["errors"]
            # Remove rows with empty file names or titles
            if recovered_from_parse_error or any("Found empty file names" in error for error in errors):
                if FilesColumns.FILE_NAME.value in files_data.columns:
                    before = len(files_data)
                    files_data = files_data.dropna(subset=[FilesColumns.FILE_NAME.value])
                    if len(files_data) != before:
                        repair_actions.append("Removed entries with empty file names")

            if recovered_from_parse_error or any("Found empty titles" in error for error in errors):
                if FilesColumns.TITLE.value in files_data.columns:
                    before = len(files_data)
                    files_data = files_data.dropna(subset=[FilesColumns.TITLE.value])
                    if len(files_data) != before:
                        repair_actions.append("Removed entries with empty titles")

            filled_empty_subtitles = False
            if FilesColumns.SUBTITLE.value in files_data.columns:
                subtitle = files_data[FilesColumns.SUBTITLE.value]
                if subtitle.isna().any():
                    files_data[FilesColumns.SUBTITLE.value] = subtitle.map(
                        lambda value: "" if pd.isna(value) else value
                    )
                    repair_actions.append("Filled empty subtitle values with empty strings")
                    filled_empty_subtitles = True

            # Remove duplicates
            if recovered_from_parse_error or any("Found duplicate file names" in error for error in errors):
                if FilesColumns.FILE_NAME.value in files_data.columns:
                    before = len(files_data)
                    files_data = files_data.drop_duplicates(subset=[FilesColumns.FILE_NAME.value], keep="first")
                    if len(files_data) != before:
                        repair_actions.append("Removed duplicate file entries")

            # Remove entries with invalid file names
            invalid_names = [
                name for name in files_data[FilesColumns.FILE_NAME.value]
                if not _is_set_basename(name)
            ]
            if invalid_names:
                files_data = files_data[~files_data[FilesColumns.FILE_NAME.value].isin(invalid_names)]
                repair_actions.append(f"Removed {len(invalid_names)} entries with invalid file names")

            # Remove entries for missing files (resolve via FilePathManager, same as validate)
            missing_files = [
                name
                for name in files_data[FilesColumns.FILE_NAME.value]
                if not os.path.exists(FilePathManager.get_csv_path(str(name)))
            ]
            if missing_files:
                files_data = files_data[~files_data[FilesColumns.FILE_NAME.value].isin(missing_files)]
                repair_actions.append(f"Removed {len(missing_files)} entries for files that don't exist")

            # Save the cleaned data if changes were made
            if (
                recovered_from_parse_error
                or column_actions
                or len(files_data) != original_len
                or filled_empty_subtitles
            ):
                files_data = ensure_files_catalog_columns(files_data, persist=False)
                files_data.to_csv(FilePathManager.get_files_data_path(), index=False)
                repair_actions.append(f"Saved repaired files.csv with {len(files_data)} entries (originally {original_len})")
            else:
                ensure_files_catalog_columns(files_data)

            return {
                "repair_actions": repair_actions,
                "success": True if repair_actions else False,
            }

        return {
            "repair_actions": ["No repairs were made"],
            "success": False,
        }
