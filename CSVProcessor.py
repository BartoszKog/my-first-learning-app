import pandas as pd
from constants import PartsOfSpeech, WordDefinitions, StatsColumns, Warnings, Errors, MAX_ROWS
from AppData import load_set, add_new_file, save_set, get_file_names
from PageProperties import PageProperties
from flet import PagePlatform

class CSVProcessor:
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
        df = df.drop(columns=[col.value for col in StatsColumns])
        df = CSVProcessor.__add_statistics_columns(df)
        return df
    
    @staticmethod
    def __sanitize_file_name(file_name: str, suffix: str) -> str:
        # remove suffix from the file name
        file_name = file_name[:-len(suffix)]
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
        
        chosen_suffix = None
        # remove suffix from the file name
        for suffix in suffixes:
            if imported_file_name.endswith(suffix):
                chosen_suffix = suffix
                break
            
        base_name = CSVProcessor.__sanitize_file_name(imported_file_name, chosen_suffix)
        
        # check if the file name is occupied by another file, if so, add a number before the suffix
        file_names_in_app_data = get_file_names()
        if base_name in file_names_in_app_data:
            i = 1
            base_without_suffix = base_name[:-len(chosen_suffix)] if chosen_suffix else base_name
            while f"{base_without_suffix}{i}{chosen_suffix}" in file_names_in_app_data:
                i += 1
            base_name = f"{base_without_suffix}{i}{chosen_suffix}"
        return base_name    
        
    
    @staticmethod
    def save_set_with_no_specific_actions(
        file_path: str,
        file_name: str, 
        title: str, 
        subtitle: str, 
        has_statistics: bool,
        keep_statistics: bool = False,
    ) -> None:
        # Replace assertions with proper error handling
        if file_path is None:
            raise ValueError("file_path cannot be None")
        if file_name is None:
            raise ValueError("file_name cannot be None")
        
        df = load_set(file_path)
        
        if not has_statistics:
            df = CSVProcessor.__add_statistics_columns(df)
        else:
            if not keep_statistics:
                df = CSVProcessor.__reset_statistics_columns(df)
        
        file_name = CSVProcessor.__create_appropriate_file_name(file_name)
        add_new_file(file_name, title, subtitle)
        save_set(df, file_name)
        
    
    @staticmethod
    def __indexes_of_rows_with_insufficient_non_empty_values(df: pd.DataFrame, data_type: str) -> list:
        # raising exception if data_type is not implemented
        if data_type not in ["words", "definitions"]:
            raise ValueError(f"data_type {data_type} is not implemented")
        # get the indexes of rows with insufficient non-empty values
        if data_type == "words":
            typical_columns = [col.value for col in PartsOfSpeech]
        elif data_type == "definitions":
            typical_columns = [col.value for col in WordDefinitions]
        else:
            raise ValueError(f"data_type {data_type} is not implemented")
        indexes = df[typical_columns].isnull().sum(axis=1) >= (len(typical_columns) - 1)
    
        return indexes.index[indexes].tolist()

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
    ) -> None:
        # Replace assertions with proper error handling
        if file_path is None:
            raise ValueError("file_path cannot be None")
        if file_name is None:
            raise ValueError("file_name cannot be None")
        if data_type is None:
            raise ValueError("data_type cannot be None")
        
        information_after_processing = ""
        
        # not implemented data_type exception
        if data_type not in ["words", "definitions"]:
            raise ValueError(f"data_type {data_type} is not implemented")
         
        
        # read the file based on index warning
        index_present = not Warnings.FIRST_COLUMN_NOT_INDEX.value in warnings
        if index_present:
            df = pd.read_csv(file_path, index_col=0)
        else:
            df = pd.read_csv(file_path)
        
        # sort out rows with empty values in typical columns
        insufficient_non_empty_values_indexes = Warnings.INSUFFICIENT_NON_EMPTY_VALUES.value in warnings
        if insufficient_non_empty_values_indexes:
            indexes = CSVProcessor.__indexes_of_rows_with_insufficient_non_empty_values(df, data_type)
            df = df.drop(indexes)
            
        # if there are any warnings about statistics, drop the statistics columns
        statistics_warnings = [
            Warnings.COLUMN_NOT_BOOLEAN.value,
            Warnings.COLUMN_NOT_INTEGER.value,
            Warnings.EMPTY_VALUES_STATISTICS.value
        ]
        if any(warning in warnings for warning in statistics_warnings):
            information_after_processing += "Statistics columns have errors, so progress information cannot be added. The set will be added to the application without progress data."
            if has_statistics:
                # Check which statistics columns actually exist before dropping
                stat_cols_to_drop = [col.value for col in StatsColumns if col.value in df.columns]
                if stat_cols_to_drop:
                    df = df.drop(columns=stat_cols_to_drop)
                has_statistics = False
                
        # Helper function to keep only necessary columns
        def keep_necessary_columns(df: pd.DataFrame, data_type: str) -> pd.DataFrame:
            if data_type == "words":
                cols_to_keep = [col.value for col in PartsOfSpeech if col.value in df.columns]
                return df[cols_to_keep]
            elif data_type == "definitions":
                cols_to_keep = [col.value for col in WordDefinitions if col.value in df.columns]
                return df[cols_to_keep]
            else:
                raise ValueError(f"data_type {data_type} is not implemented")
        
        if not has_statistics:
            df = keep_necessary_columns(df, data_type)    
            df = CSVProcessor.__add_statistics_columns(df)
        else:
            if not keep_statistics:
                df = keep_necessary_columns(df, data_type)
                df = CSVProcessor.__reset_statistics_columns(df)
            else:
                # Check which statistics columns actually exist before selecting
                stat_cols = [col.value for col in StatsColumns if col.value in df.columns]
                if len(stat_cols) == len(StatsColumns):  # Only proceed if all statistics columns exist
                    statistics_df = df[stat_cols]
                    df = keep_necessary_columns(df, data_type)
                    df = pd.concat([df, statistics_df], axis=1)
                else:
                    # If some statistics columns are missing, reset them
                    df = keep_necessary_columns(df, data_type)
                    df = CSVProcessor.__add_statistics_columns(df)
                
        # preparing file name
        warnings_file_name = [
            Warnings.FILE_NAME_PATTERN_WORDS.value,
            Warnings.FILE_NAME_PATTERN_DEFINITIONS.value
        ]
        
        unappropriated_file_name = any(warning in warnings for warning in warnings_file_name)
        
        if not unappropriated_file_name:
            file_name = CSVProcessor.__create_appropriate_file_name(file_name)
        else:
            file_name = CSVProcessor.__sanitize_file_name(file_name, "")
            file_name += f"_{data_type}.csv"
            file_name = CSVProcessor.__create_appropriate_file_name(file_name)
            
        add_new_file(file_name, title, subtitle)
        save_set(df, file_name)
        return information_after_processing
                
    
    @staticmethod
    def validate_file(file_path: str) -> dict:
        # Function for validating the file of the given path
        errors = []
        warnings = []
        is_valid = True
        requires_specific_actions = False
        has_statistics = False
        name_suggestion = ""
        data_type = ""

        data_conventions = [
            ("words", "_words.csv", PartsOfSpeech, Errors.MISSING_COLUMNS_WORDS, Warnings.FILE_NAME_PATTERN_WORDS),
            ("definitions", "_definitions.csv", WordDefinitions, Errors.MISSING_COLUMNS_DEFINITIONS, Warnings.FILE_NAME_PATTERN_DEFINITIONS)
        ]

        # Ensure proper validation of data_conventions entries
        for convention in data_conventions:
            if len(convention) != 5:
                raise ValueError("Each data convention must have exactly 5 elements.")
            if not isinstance(convention[0], str):
                raise TypeError("The first element of each data convention must be a string (data type).")
            if not isinstance(convention[1], str):
                raise TypeError("The second element of each data convention must be a string (file suffix).")
            if not hasattr(convention[2], '__members__'):
                raise TypeError("The third element of each data convention must be an Enum (columns enum).")
            if not isinstance(convention[3], Errors):
                raise TypeError("The fourth element of each data convention must be an Errors enum member.")
            if not isinstance(convention[4], Warnings):
                raise TypeError("The fifth element of each data convention must be a Warnings enum member.")

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
        if not file_path.endswith('.csv'):
            errors.append(Errors.NOT_A_CSV.value)
            is_valid = False
        else:
            # Try to load the file with pandas
            try:
                df = pd.read_csv(file_path)
            except FileNotFoundError:
                errors.append(Errors.FILE_NOT_FOUND.value)
                is_valid = False
            except Exception as e:
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

        # Validate column names based on file name
        if is_valid:
            for convention, suffix, columns_enum, missing_columns_error, pattern_warning in data_conventions:
                if file_path.endswith(suffix):
                    expected_columns = {col.value for col in columns_enum}
                    data_type = convention
                    if not validate_columns(expected_columns, df.columns, missing_columns_error):
                        is_valid = False
                        
                    file_separator = '\\' if PageProperties.platform == PagePlatform.WINDOWS else '/'
                        
                    name_suggestion = file_path.split(suffix)[0].split(file_separator)[-1] # android can be different
                    break
            else:
                # Check if columns match either words or definitions
                words_columns = {col.value for col in PartsOfSpeech}
                definitions_columns = {col.value for col in WordDefinitions}
                if words_columns.issubset(df.columns):
                    warnings.append(Warnings.FILE_NAME_PATTERN_WORDS.value)
                    requires_specific_actions = True
                    validate_columns(words_columns, df.columns, Errors.MISSING_COLUMNS_WORDS)
                    data_type = "words"
                elif definitions_columns.issubset(df.columns):
                    warnings.append(Warnings.FILE_NAME_PATTERN_DEFINITIONS.value)
                    requires_specific_actions = True
                    validate_columns(definitions_columns, df.columns, Errors.MISSING_COLUMNS_DEFINITIONS)
                    data_type = "definitions"
                else:
                    errors.append("File does not match any expected column patterns.")
                    is_valid = False

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
            typical_columns = [col for col in typical_columns if col in df.columns]  # Only check columns that exist
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

        # Remove duplicate warnings
        warnings = list(set(warnings))

        return {
            "errors": errors,
            "warnings": warnings,
            "is_valid": is_valid,
            "requires_specific_actions": requires_specific_actions,
            "has_statistics": has_statistics,
            "name_suggestion": name_suggestion,
            "data_type": data_type
        }


