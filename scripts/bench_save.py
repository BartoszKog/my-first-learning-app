"""Measure how long set saves take, stage by stage, without touching real data.

Every scenario runs in a fresh Python process so the first ("cold") pass sees
the same state as the first action after starting the app. The same process
then repeats the scenario ("warm"). All work happens on a temporary copy of
the storage directory; ``--copy-from`` only reads the source.

Usage::

    uv run python scripts/bench_save.py
    uv run python scripts/bench_save.py --real
    uv run python scripts/bench_save.py --copy-from "C:\\path\\to\\storage\\data"
    uv run python scripts/bench_save.py --tts-files 3000 --runs 5 --json result.json
    uv run python scripts/bench_save.py --profile

``--real`` copies ``.flet/storage/data`` from this project, where ``flet run``
keeps the app data during development. An installed app keeps it in the
folder Flet passes as ``FLET_APP_STORAGE_DATA``; pass that to ``--copy-from``.

Scenarios:
    edit_create  first Save of a new set in Edit (create_data_file_words + save_set)
    edit_resave  Save after changing one card in Edit, then reloading the cards
    import_csv   import a picked CSV (validate_file + save_set_with_no_specific_actions)
    home_refresh catalog plus learn progress for every tile on Home
"""

from __future__ import annotations

import argparse
import cProfile
import functools
import io
import json
import os
import platform
import pstats
import random
import shutil
import statistics
import subprocess
import sys
import tempfile
import time
from collections import defaultdict
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = REPO_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

DEV_DATA_DIR = REPO_ROOT / ".flet" / "storage" / "data"
SCENARIOS = ("edit_create", "edit_resave", "import_csv", "home_refresh")
WORDS_COLUMNS = ("verb", "person", "thing", "adjective", "adverb")
STATS_DEFAULTS = {
    "correct_answers": 0,
    "good_answers_in_a_row": False,
    "good_answer": False,
    "word_to_learn": False,
    "checks": 0,
}
SYLLABLES = ("ka", "lo", "mi", "ra", "te", "su", "no", "vi", "da", "pe", "go", "zu")


def _word(rng: random.Random) -> str:
    return "".join(rng.choice(SYLLABLES) for _ in range(rng.randint(2, 4)))


def _words_row(rng: random.Random) -> dict:
    row = {column: None for column in WORDS_COLUMNS}
    for column in rng.sample(WORDS_COLUMNS, rng.randint(2, 4)):
        row[column] = "/".join(_word(rng) for _ in range(rng.randint(1, 2)))
    return row


def _definitions_row(rng: random.Random) -> dict:
    return {
        "definition": " ".join(_word(rng) for _ in range(rng.randint(4, 8))),
        "word": _word(rng),
    }


# --------------------------------------------------------------------------
# Instrumentation (worker process)
# --------------------------------------------------------------------------


class Recorder:
    """Inclusive wall time, call count, SQL statements, and commits per label."""

    def __init__(self) -> None:
        self.sql = 0
        self.commits = 0
        self.stats: dict[str, dict] = defaultdict(lambda: {"ms": 0.0, "calls": 0, "sql": 0, "commits": 0})
        self._active: set[str] = set()

    def wrap(self, label: str, func):
        recorder = self

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            if label in recorder._active:
                return func(*args, **kwargs)
            recorder._active.add(label)
            sql_before, commits_before = recorder.sql, recorder.commits
            start = time.perf_counter()
            try:
                return func(*args, **kwargs)
            finally:
                entry = recorder.stats[label]
                entry["ms"] += (time.perf_counter() - start) * 1000
                entry["calls"] += 1
                entry["sql"] += recorder.sql - sql_before
                entry["commits"] += recorder.commits - commits_before
                recorder._active.discard(label)

        wrapper.__bench_original__ = func
        return wrapper

    def snapshot_and_reset(self) -> dict:
        data = {label: dict(values) for label, values in self.stats.items()}
        self.stats.clear()
        return data


def _patch_everywhere(original, wrapper) -> None:
    """Replace ``original`` in every loaded ``learning_app`` module namespace.

    Many call sites use ``from module import name``, so patching the defining
    module alone would miss them.
    """
    for name, module in list(sys.modules.items()):
        if not name.startswith("learning_app") or module is None:
            continue
        for attr, value in list(vars(module).items()):
            if value is original:
                setattr(module, attr, wrapper)


def _instrument(recorder: Recorder) -> None:
    from sqlalchemy import event

    import learning_app.tts.service as tts_service
    import learning_app.tts.texts as tts_texts
    from learning_app.data import (
        app_data,
        csv_processor,
        demo_sets,
        repository,
        set_settings,
    )
    from learning_app.tts.cache import TtsCache

    targets = [
        (repository, "save_set_frame", "repository.save_set_frame"),
        (repository, "load_set_frame", "repository.load_set_frame"),
        (repository, "add_set", "repository.add_set"),
        (repository, "list_catalog", "repository.list_catalog"),
        (repository, "iter_speakable_sets", "repository.iter_speakable_sets"),
        (repository, "get_learning_set", "repository.get_learning_set"),
        (app_data, "save_set", "app_data.save_set"),
        (app_data, "load_set", "app_data.load_set"),
        (app_data, "add_new_file", "app_data.add_new_file"),
        (app_data, "get_file_names_and_titles", "app_data.get_file_names_and_titles"),
        (app_data, "get_set_learn_progress", "app_data.get_set_learn_progress"),
        (demo_sets, "allocate_unique_set_basename", "demo_sets.allocate_unique_set_basename"),
        (set_settings, "language_for_set_file", "set_settings.language_for_set_file"),
        (tts_service, "garbage_collect_tts_cache", "tts.garbage_collect_tts_cache"),
        (tts_texts, "collect_speakable_texts", "tts.collect_speakable_texts"),
    ]
    for module, attr, label in targets:
        original = getattr(module, attr, None)
        if original is None:
            continue
        _patch_everywhere(original, recorder.wrap(label, original))

    TtsCache.garbage_collect = recorder.wrap("TtsCache.garbage_collect (disk scan)", TtsCache.garbage_collect)

    processor = csv_processor.CSVProcessor
    for attr in ("validate_file", "save_set_with_no_specific_actions"):
        original = getattr(processor, attr)
        setattr(processor, attr, staticmethod(recorder.wrap(f"CSVProcessor.{attr}", original)))

    original_create = app_data.AppData.create_data_file_words
    app_data.AppData.create_data_file_words = staticmethod(
        recorder.wrap("AppData.create_data_file_words", original_create)
    )

    engine = repository.get_engine()

    @event.listens_for(engine, "before_cursor_execute")
    def _count_sql(*_args, **_kwargs):
        recorder.sql += 1

    @event.listens_for(engine, "commit")
    def _count_commit(*_args, **_kwargs):
        recorder.commits += 1


# --------------------------------------------------------------------------
# Scenarios (worker process). Each mirrors what the screen handler calls.
# --------------------------------------------------------------------------


def _edit_values(rng: random.Random) -> dict:
    values = _words_row(rng)
    values.update(STATS_DEFAULTS)
    return values


def scenario_edit_create(pass_index: int, rng: random.Random, workdir: Path) -> None:
    """Same calls as ``EditSetMenu.__save_changes`` on the first save of a new set."""
    import pandas as pd

    from learning_app.data.app_data import AppData, create_empty_set, save_set

    file_name = f"BenchCreate{pass_index}_words.csv"
    existing = create_empty_set("words")
    new_df = pd.DataFrame([_edit_values(rng) for _ in range(10)], columns=[*WORDS_COLUMNS, *STATS_DEFAULTS])
    data = pd.concat([existing, new_df], ignore_index=True).reset_index(drop=True)
    AppData.create_data_file_words(file_name, title=f"Bench create {pass_index}", subtitle="")
    save_set(data, file_name, prune_tts=True)


def scenario_edit_resave(pass_index: int, rng: random.Random, workdir: Path) -> None:
    """Change one card of an existing set, save, then reload like ``__reload_cards``."""
    import pandas as pd

    from learning_app.data.app_data import get_file_names, load_set, save_set

    names = sorted(name for name in get_file_names() if name.endswith("_words.csv"))
    if not names:
        raise RuntimeError("edit_resave needs at least one *_words.csv set in the data copy.")
    file_name = names[pass_index % len(names)]
    existing = load_set(file_name)
    changed_index = existing.index[0]
    existing = existing.drop(changed_index)
    new_df = pd.DataFrame([_edit_values(rng)], columns=[*WORDS_COLUMNS, *STATS_DEFAULTS])
    data = pd.concat([existing, new_df], ignore_index=True).reset_index(drop=True)
    save_set(data, file_name, prune_tts=True)
    load_set(file_name)


def scenario_import_csv(pass_index: int, rng: random.Random, workdir: Path) -> None:
    """Validate and import a picked CSV with no warnings, like ``__on_add_set_click``."""
    import pandas as pd

    from learning_app.data.csv_processor import CSVProcessor

    picked = workdir / f"BenchImport{pass_index}_words.csv"
    pd.DataFrame([_words_row(rng) for _ in range(30)], columns=list(WORDS_COLUMNS)).to_csv(picked, index=True)
    result = CSVProcessor.validate_file(str(picked), original_name=picked.name)
    if not result["is_valid"]:
        raise RuntimeError(f"Generated CSV failed validation: {result['errors']}")
    if result["requires_specific_actions"]:
        raise RuntimeError(f"Generated CSV needs repair: {result['warnings']}")
    CSVProcessor.save_set_with_no_specific_actions(
        str(picked), picked.name, f"Bench import {pass_index}", "", result["has_statistics"]
    )


def scenario_home_refresh(pass_index: int, rng: random.Random, workdir: Path) -> None:
    """Catalog plus one ``get_set_learn_progress`` per tile, like ``TilesContainer.refresh_content``."""
    from learning_app.data.app_data import (
        get_file_names_and_titles,
        get_set_learn_progress,
    )
    from learning_app.data.constants import FilesColumns

    for entry in get_file_names_and_titles():
        get_set_learn_progress(entry[FilesColumns.FILE_NAME.value])


SCENARIO_FUNCS = {
    "edit_create": scenario_edit_create,
    "edit_resave": scenario_edit_resave,
    "import_csv": scenario_import_csv,
    "home_refresh": scenario_home_refresh,
}


def _count_tts_files(data_dir: Path) -> int:
    root = data_dir / "tts_cache"
    return sum(1 for _ in root.rglob("*.mp3")) if root.is_dir() else 0


def run_worker(scenario: str, data_dir: Path, out_path: Path, profile_path: Path | None) -> None:
    """Run one scenario cold then warm in this (fresh) process and write JSON."""
    result: dict = {"scenario": scenario, "passes": []}

    start = time.perf_counter()
    from learning_app.data.file_path_manager import FilePathManager

    import_ms = None
    try:
        from learning_app.data import repository
    except ImportError as exc:
        raise SystemExit(
            "This script needs the SQLite storage (learning_app.data.repository). "
            f"Import failed: {exc}"
        ) from exc
    import learning_app.data.app_data
    import learning_app.data.csv_processor
    import learning_app.tts.service  # noqa: F401
    import_ms = (time.perf_counter() - start) * 1000

    assert Path(FilePathManager.get_data_dir()).resolve() == data_dir.resolve(), "storage is not isolated"

    start = time.perf_counter()
    repository.init_db()
    init_ms = (time.perf_counter() - start) * 1000
    result["startup"] = {"imports_ms": import_ms, "init_db_ms": init_ms}

    recorder = Recorder()
    _instrument(recorder)
    rng = random.Random(1234)
    func = SCENARIO_FUNCS[scenario]

    for pass_index, label in enumerate(("cold", "warm")):
        tts_before = _count_tts_files(data_dir)
        recorder.sql = recorder.commits = 0
        profiler = cProfile.Profile() if profile_path is not None and label == "cold" else None
        start = time.perf_counter()
        if profiler is not None:
            profiler.enable()
        func(pass_index, rng, data_dir)
        if profiler is not None:
            profiler.disable()
            profiler.dump_stats(str(profile_path))
        total_ms = (time.perf_counter() - start) * 1000
        result["passes"].append(
            {
                "label": label,
                "total_ms": total_ms,
                "sql": recorder.sql,
                "commits": recorder.commits,
                "tts_files_before": tts_before,
                "tts_files_after": _count_tts_files(data_dir),
                "stages": recorder.snapshot_and_reset(),
            }
        )

    out_path.write_text(json.dumps(result), encoding="utf-8")


# --------------------------------------------------------------------------
# Dataset preparation (parent process, on a temporary template directory)
# --------------------------------------------------------------------------


def _isolate_in_process(data_dir: Path) -> None:
    from learning_app.data.repository import reset_storage

    from learning_app.data.file_path_manager import FilePathManager

    csv_dir = data_dir / "csv_files"
    csv_dir.mkdir(parents=True, exist_ok=True)
    FilePathManager._data_dir = str(data_dir)
    FilePathManager._temp_dir = str(data_dir.parent / "temp")
    FilePathManager._csv_dir = str(csv_dir)
    FilePathManager._initialized = True
    reset_storage()


def build_synthetic_dataset(template: Path, sets: int, cards: int, tts_files: int, seed: int) -> None:
    import pandas as pd
    from learning_app.data.repository import init_db, reset_storage

    from learning_app.data.app_data import add_new_file, save_set
    from learning_app.tts.cache import TtsCache
    from learning_app.tts.texts import speakable_phrases
    from learning_app.ui.tts_preferences import TtsPreferences

    _isolate_in_process(template)
    init_db()
    rng = random.Random(seed)
    phrases: list[str] = []
    for index in range(sets):
        kind = "words" if index % 2 == 0 else "definitions"
        rows = [(_words_row(rng) if kind == "words" else _definitions_row(rng)) for _ in range(cards)]
        frame = pd.DataFrame(rows)
        for column, value in STATS_DEFAULTS.items():
            frame[column] = value
        file_name = f"Synthetic{index}_{kind}.csv"
        add_new_file(file_name, f"Synthetic {index}", "")
        save_set(frame, file_name)
        for row in rows:
            for value in row.values():
                if value:
                    phrases.extend(speakable_phrases(value))

    language = TtsPreferences.language
    unique_live = list(dict.fromkeys(phrases))
    cache = TtsCache(template / "tts_cache")
    fake_mp3 = b"ID3" + bytes(2000)
    for index in range(tts_files):
        if index < len(unique_live):
            text = unique_live[index]
        else:
            text = f"orphan phrase {index}"
        key = cache.make_key(provider="gtts", language=language, text=text)
        cache.put(key, fake_mp3, text=text, language=language, provider="gtts")
    reset_storage()


def copy_real_dataset(source: Path, template: Path) -> None:
    template.mkdir(parents=True, exist_ok=True)
    copied = []
    for name in ("learning.sqlite", "learning.sqlite-wal", "learning.sqlite-shm"):
        if (source / name).is_file():
            shutil.copy2(source / name, template / name)
            copied.append(name)
    for folder in ("csv_files", "tts_cache"):
        if (source / folder).is_dir():
            shutil.copytree(source / folder, template / folder)
            copied.append(folder + "/")
    (template / "csv_files").mkdir(exist_ok=True)
    if "learning.sqlite" not in copied:
        raise SystemExit(
            f"No learning.sqlite in {source}. Start the app once with the SQLite version, "
            "or pass the folder that contains learning.sqlite to --copy-from."
        )
    print(f"Copied from {source}: {', '.join(copied)}")


def describe_dataset(template: Path) -> dict:
    import sqlite3

    db = template / "learning.sqlite"
    info = {"db_kb": round(db.stat().st_size / 1024, 1) if db.exists() else 0}
    with sqlite3.connect(db) as connection:
        info["sets"] = connection.execute("select count(*) from learning_set").fetchone()[0]
        info["cards"] = connection.execute("select count(*) from card").fetchone()[0]
    info["tts_mp3"] = _count_tts_files(template)
    return info


# --------------------------------------------------------------------------
# Reporting
# --------------------------------------------------------------------------


def _median(values: list[float]) -> float:
    return statistics.median(values) if values else 0.0


def aggregate(results: list[dict]) -> dict:
    summary: dict = {}
    for scenario in SCENARIOS:
        runs = [run for run in results if run["scenario"] == scenario]
        if not runs:
            continue
        entry = {
            "runs": len(runs),
            "imports_ms": _median([run["startup"]["imports_ms"] for run in runs]),
            "init_db_ms": _median([run["startup"]["init_db_ms"] for run in runs]),
            "passes": {},
        }
        for label in ("cold", "warm"):
            passes = [next(p for p in run["passes"] if p["label"] == label) for run in runs]
            stage_names = sorted({name for p in passes for name in p["stages"]})
            entry["passes"][label] = {
                "total_ms": _median([p["total_ms"] for p in passes]),
                "total_ms_all_runs": [round(p["total_ms"], 1) for p in passes],
                "sql": passes[0]["sql"],
                "commits": passes[0]["commits"],
                "tts_files_before": passes[0]["tts_files_before"],
                "tts_files_after": passes[0]["tts_files_after"],
                "stages": {
                    name: {
                        "ms": _median([p["stages"].get(name, {}).get("ms", 0.0) for p in passes]),
                        "calls": passes[0]["stages"].get(name, {}).get("calls", 0),
                        "sql": passes[0]["stages"].get(name, {}).get("sql", 0),
                        "commits": passes[0]["stages"].get(name, {}).get("commits", 0),
                    }
                    for name in stage_names
                },
            }
        summary[scenario] = entry
    return summary


def print_report(summary: dict, dataset: dict) -> None:
    print()
    print(
        f"Data: {dataset['sets']} sets, {dataset['cards']} cards, "
        f"{dataset['tts_mp3']} cached MP3s, DB {dataset['db_kb']} KB"
    )
    print(f"Python {platform.python_version()} on {platform.system()} {platform.release()}")
    for scenario, entry in summary.items():
        cold = entry["passes"]["cold"]
        warm = entry["passes"]["warm"]
        print()
        print(f"== {scenario}  (median of {entry['runs']} fresh processes)")
        print(
            f"   startup before the click: imports {entry['imports_ms']:.0f} ms, "
            f"init_db {entry['init_db_ms']:.0f} ms (paid at app start, not on the click)"
        )
        print(
            f"   TOTAL  cold {cold['total_ms']:8.1f} ms  warm {warm['total_ms']:8.1f} ms   "
            f"SQL {cold['sql']}/{warm['sql']}  tx {cold['commits']}/{warm['commits']}   "
            f"runs cold={cold['total_ms_all_runs']}"
        )
        if cold["tts_files_before"] != cold["tts_files_after"]:
            print(
                f"   TTS GC removed {cold['tts_files_before'] - cold['tts_files_after']} orphan MP3s on the cold pass"
            )
        print(f"   {'stage (inclusive time)':44} {'calls':>5} {'cold ms':>9} {'warm ms':>9} {'SQL c/w':>9} {'tx':>4}")
        names = sorted(cold["stages"], key=lambda n: -cold["stages"][n]["ms"])
        for name in names:
            c = cold["stages"][name]
            w = warm["stages"].get(name, {"ms": 0.0, "sql": 0})
            print(
                f"   {name:44} {c['calls']:>5} {c['ms']:>9.1f} {w['ms']:>9.1f} "
                f"{str(c['sql']) + '/' + str(w['sql']):>9} {c['commits']:>4}"
            )
    print()
    print("Stages are nested (inclusive), so their times do not add up to TOTAL.")
    print("tx counts committed sessions, read-only ones included; only write transactions hit the disk.")


def print_profile(path: Path, limit: int = 25) -> None:
    buffer = io.StringIO()
    stats = pstats.Stats(str(path), stream=buffer)
    stats.strip_dirs().sort_stats("cumulative").print_stats(limit)
    print(buffer.getvalue())


# --------------------------------------------------------------------------
# Entry point
# --------------------------------------------------------------------------


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--copy-from", type=Path, help="Storage folder with learning.sqlite (read only, copied).")
    parser.add_argument("--real", action="store_true", help=f"Same as --copy-from {DEV_DATA_DIR}.")
    parser.add_argument("--sets", type=int, default=30, help="Synthetic sets (default 30).")
    parser.add_argument("--cards", type=int, default=30, help="Cards per synthetic set, max 40 (default 30).")
    parser.add_argument("--tts-files", type=int, default=500, help="Synthetic cached MP3s (default 500).")
    parser.add_argument("--runs", type=int, default=3, help="Fresh processes per scenario (default 3).")
    parser.add_argument("--scenario", choices=SCENARIOS, action="append", help="Run only these scenarios.")
    parser.add_argument("--json", type=Path, help="Write the aggregated result to this file.")
    parser.add_argument("--profile", action="store_true", help="cProfile the cold pass; print the slowest one.")
    parser.add_argument("--keep", action="store_true", help="Keep the temporary folder and print its path.")
    parser.add_argument(
        "--work-dir",
        type=Path,
        help="Parent folder for the temporary copy. Use the same disk as the real data to include its fsync cost.",
    )
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--_worker", nargs=3, metavar=("SCENARIO", "DATA_DIR", "OUT"), help=argparse.SUPPRESS)
    parser.add_argument("--_profile-out", type=Path, help=argparse.SUPPRESS)
    args = parser.parse_args()

    if args._worker:
        scenario, data_dir, out = args._worker
        run_worker(scenario, Path(data_dir), Path(out), args._profile_out)
        return

    if args.real:
        args.copy_from = DEV_DATA_DIR
    if args.cards > 40:
        parser.error("--cards cannot exceed 40 (MAX_ROWS); import validation would reject the set.")

    try:
        import learning_app.data.repository  # noqa: F401
    except ImportError as exc:
        raise SystemExit(f"This script needs the SQLite storage (learning_app.data.repository): {exc}") from exc

    scenarios = args.scenario or list(SCENARIOS)
    if args.work_dir:
        args.work_dir.mkdir(parents=True, exist_ok=True)
    root = Path(tempfile.mkdtemp(prefix="bench_save_", dir=args.work_dir))
    template = root / "template"
    try:
        if args.copy_from:
            copy_real_dataset(args.copy_from, template)
        else:
            print(f"Building synthetic data: {args.sets} sets x {args.cards} cards, {args.tts_files} MP3s ...")
            build_synthetic_dataset(template, args.sets, args.cards, args.tts_files, args.seed)
        dataset = describe_dataset(template)

        results = []
        profiles: dict[str, Path] = {}
        for scenario in scenarios:
            for run in range(args.runs):
                run_dir = root / f"{scenario}_{run}"
                data_dir = run_dir / "data"
                shutil.copytree(template, data_dir)
                out = run_dir / "result.json"
                env = dict(os.environ)
                env["FLET_APP_STORAGE_DATA"] = str(data_dir)
                env["FLET_APP_STORAGE_TEMP"] = str(run_dir / "temp")
                command = [sys.executable, str(Path(__file__).resolve()), "--_worker", scenario, str(data_dir), str(out)]
                if args.profile and run == 0:
                    profiles[scenario] = run_dir / "cold.prof"
                    command += ["--_profile-out", str(profiles[scenario])]
                print(f"  {scenario} run {run + 1}/{args.runs}", flush=True)
                subprocess.run(command, check=True, env=env, cwd=str(run_dir))
                results.append(json.loads(out.read_text(encoding="utf-8")))

        summary = aggregate(results)
        print_report(summary, dataset)

        if args.profile and profiles:
            slowest = max(profiles, key=lambda s: summary[s]["passes"]["cold"]["total_ms"])
            print(f"cProfile of the slowest cold pass ({slowest}), top 25 by cumulative time:")
            print_profile(profiles[slowest])

        if args.json:
            args.json.write_text(
                json.dumps({"dataset": dataset, "scenarios": summary, "raw": results}, indent=2),
                encoding="utf-8",
            )
            print(f"Wrote {args.json}")
    finally:
        if args.keep:
            print(f"Temporary data kept in {root}")
        else:
            shutil.rmtree(root, ignore_errors=True)


if __name__ == "__main__":
    main()
