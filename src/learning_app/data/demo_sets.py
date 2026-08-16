"""Bundled demo learning sets: registry, reserved names, and install helpers.

Demo CSV templates live under the app assets directory. Installation copies them
into ``csv_files/`` with fixed basenames and registers catalog rows. Those
basenames stay reserved so create/import cannot claim them.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

import pandas as pd

from learning_app.data.app_data import add_new_file, get_file_names, save_set, set_file_exists
from learning_app.data.constants import StatsColumns

DEMO_SETS: list[dict[str, str]] = [
    {
        "file_name": "DemoWordFormation_words.csv",
        "title": "Demo Word formation",
        "subtitle": "Sample set",
        "asset_relative": "demos/DemoWordFormation_words.csv",
    },
    {
        "file_name": "DemoEnDefinitions_definitions.csv",
        "title": "Demo EN definitions",
        "subtitle": "Sample set",
        "asset_relative": "demos/DemoEnDefinitions_definitions.csv",
    },
    {
        "file_name": "DemoEnPl_definitions.csv",
        "title": "Demo EN-PL",
        "subtitle": "Sample set",
        "asset_relative": "demos/DemoEnPl_definitions.csv",
    },
]

RESERVED_DEMO_SET_NAMES: frozenset[str] = frozenset(demo["file_name"] for demo in DEMO_SETS)


@dataclass
class DemoInstallResult:
    """Outcome of ``install_demo_sets`` for UI messaging."""

    added: list[str] = field(default_factory=list)
    skipped: list[str] = field(default_factory=list)


def get_assets_dir() -> Path:
    """Return the absolute assets directory for local runs and ``flet build``."""
    env = os.environ.get("FLET_ASSETS_DIR")
    if env:
        return Path(env).resolve()
    # ``demo_sets.py`` → ``data/`` → ``learning_app/`` → ``src/`` → ``src/assets``
    return (Path(__file__).resolve().parents[2] / "assets").resolve()


def resolve_demo_asset_path(relative: str) -> Path:
    """Resolve a path under assets (for example ``demos/Foo_words.csv``)."""
    return get_assets_dir() / relative


def is_set_name_reserved(file_name: str) -> bool:
    """Return whether ``file_name`` is a reserved demo basename."""
    return os.path.basename(file_name) in RESERVED_DEMO_SET_NAMES


def is_demo_already_installed(file_name: str, existing_basenames: list[str] | None = None) -> bool:
    """Return whether a demo basename is already in the catalog or on disk."""
    basename = os.path.basename(file_name)
    names = existing_basenames if existing_basenames is not None else get_file_names()
    if basename in names:
        return True
    return set_file_exists(basename)


def is_set_name_taken(file_name: str, existing_basenames: list[str] | None = None) -> bool:
    """Return whether a set basename is reserved, catalogued, or present on disk.

    Used when allocating names for create/import so reserved demo basenames
    cannot be claimed. Demo installation uses ``is_demo_already_installed``
    instead (reserved names are expected for demos).
    """
    basename = os.path.basename(file_name)
    if basename in RESERVED_DEMO_SET_NAMES:
        return True
    return is_demo_already_installed(basename, existing_basenames)


def allocate_unique_set_basename(preferred_basename: str) -> str:
    """Return a free ``*_words.csv`` / ``*_definitions.csv`` basename.

    Reserved demo names, catalog entries, and on-disk files are treated as
    occupied. When ``preferred_basename`` is taken, appends ``1``, ``2``, …
    before the kind suffix.
    """
    if preferred_basename is None:
        raise ValueError("preferred_basename cannot be None")

    suffixes = ["_words.csv", "_definitions.csv"]
    if not any(preferred_basename.endswith(suffix) for suffix in suffixes):
        raise ValueError(
            f"preferred_basename {preferred_basename} does not end with any of the expected suffixes"
        )

    chosen_suffix = next(suffix for suffix in suffixes if preferred_basename.endswith(suffix))
    existing = get_file_names()

    if not is_set_name_taken(preferred_basename, existing):
        return preferred_basename

    stem = preferred_basename[: -len(chosen_suffix)]
    i = 1
    while True:
        candidate = f"{stem}{i}{chosen_suffix}"
        if not is_set_name_taken(candidate, existing):
            return candidate
        i += 1


def _reset_statistics(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df[StatsColumns.CORRECT_ANSWERS.value] = 0
    df[StatsColumns.GOOD_ANSWERS_IN_A_ROW.value] = False
    df[StatsColumns.GOOD_ANSWER.value] = False
    df[StatsColumns.WORD_TO_LEARN.value] = False
    return df


def install_demo_sets() -> DemoInstallResult:
    """Copy missing demo templates into storage and register them in the catalog.

    Skips a demo when its fixed basename is already in the catalog or on disk.
    Always resets learning statistics on newly installed copies.
    """
    existing = list(get_file_names())
    result = DemoInstallResult()

    for demo in DEMO_SETS:
        file_name = demo["file_name"]
        title = demo["title"]

        if is_demo_already_installed(file_name, existing):
            result.skipped.append(title)
            continue

        asset_path = resolve_demo_asset_path(demo["asset_relative"])
        if not asset_path.is_file():
            raise FileNotFoundError(f"Demo asset not found: {asset_path}")

        df = pd.read_csv(asset_path, index_col=0)
        df = _reset_statistics(df)
        save_set(df, file_name)
        add_new_file(file_name, title, demo["subtitle"])
        existing.append(file_name)
        result.added.append(title)

    return result
