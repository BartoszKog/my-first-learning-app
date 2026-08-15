"""Isolate FilePathManager so tests never touch the developer's catalog."""

from pathlib import Path

import pytest

from learning_app.data.file_path_manager import FilePathManager


@pytest.fixture(autouse=True)
def isolated_csv_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    data_dir = tmp_path / "storage_data"
    csv_dir = data_dir / "csv_files"
    csv_dir.mkdir(parents=True)

    monkeypatch.setattr(FilePathManager, "_data_dir", str(data_dir), raising=False)
    monkeypatch.setattr(FilePathManager, "_temp_dir", str(tmp_path / "storage_temp"), raising=False)
    monkeypatch.setattr(FilePathManager, "_csv_dir", str(csv_dir), raising=False)
    monkeypatch.setattr(FilePathManager, "_initialized", True)
    return csv_dir
