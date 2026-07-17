"""Resolve Flet storage directories and paths under ``csv_files/``.

``FilePathManager`` is initialized once at application startup so catalog and
set CSVs share a single directory root. Prefer these helpers over hard-coded
absolute paths.
"""

import os


class FilePathManager:
    """Manage application storage paths for CSV catalogs and learning sets.

    Reads ``FLET_APP_STORAGE_DATA`` and ``FLET_APP_STORAGE_TEMP`` from the
    environment. When the data root is unset, ``csv_files`` resolution falls
    back to the process current working directory.
    """

    _data_dir = os.getenv("FLET_APP_STORAGE_DATA")
    _temp_dir = os.getenv("FLET_APP_STORAGE_TEMP")
    _initialized = False

    @classmethod
    def initialize(cls) -> None:
        """Create the CSV directory if needed and mark the manager ready.

        Safe to call more than once; later calls are no-ops.
        """
        if cls._initialized:
            return

        if cls._data_dir:
            cls._csv_dir = os.path.join(cls._data_dir, "csv_files")
            os.makedirs(cls._csv_dir, exist_ok=True)
        else:
            # If environment variable is not available (e.g., in web mode),
            # use the current directory
            cls._csv_dir = os.getcwd()

        cls._initialized = True

    @classmethod
    def get_csv_path(cls, file_name: str) -> str:
        """Return the absolute path for a set CSV basename or path.

        Args:
            file_name: Set file basename (for example ``animals_words.csv``)
                or an absolute path already under the CSV directory.

        Returns:
            Absolute path to use for load or save.
        """
        cls.initialize()
        if cls._data_dir and os.path.dirname(file_name) and cls._csv_dir in file_name:
            return file_name
        return os.path.join(cls._csv_dir, os.path.basename(file_name))

    @classmethod
    def get_files_data_path(cls) -> str:
        """Return the absolute path of the set catalog ``files.csv``."""
        cls.initialize()
        return os.path.join(cls._csv_dir, "files.csv")

    @classmethod
    def get_data_dir(cls) -> str | None:
        """Return ``FLET_APP_STORAGE_DATA``, or ``None`` when unset."""
        cls.initialize()
        return cls._data_dir

    @classmethod
    def get_temp_dir(cls) -> str | None:
        """Return ``FLET_APP_STORAGE_TEMP``, or ``None`` when unset."""
        cls.initialize()
        return cls._temp_dir

    @classmethod
    def get_csv_dir(cls) -> str:
        """Return the directory that holds set CSVs and ``files.csv``."""
        cls.initialize()
        return cls._csv_dir
