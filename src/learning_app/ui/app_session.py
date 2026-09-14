"""Session-scoped page, picker, TTS playback, and navigation-interaction state."""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

import flet_audio as fta
from flet import FilePicker, IconButton, Page

from learning_app.ui.app_chrome import AppChrome

if TYPE_CHECKING:
    from learning_app.tts.service import TtsService


class AppSession:
    """Store process-wide UI objects and navigation-disabled state."""

    _page: Page | None = None
    _export_picker_csv: FilePicker | None = None
    _tts_service: TtsService | None = None
    _tts_player: fta.Audio | None = None
    _tts_retain: list = []
    _tts_mounted = False
    _speak_generation = 0
    _playback_done: asyncio.Event | None = None
    _src_loaded: asyncio.Event | None = None
    _navigation_disabled = False

    @classmethod
    def set_page(cls, page: Page):
        """Register the active Flet page.

        Args:
            page: Page used by session-level UI operations.
        """
        cls._page = page

    @classmethod
    def get_page(cls) -> Page:
        """Return the registered active page.

        Returns:
            The active Flet page.

        Raises:
            AssertionError: If a page has not been registered.
        """
        assert cls._page is not None, "Page is not set"
        return cls._page

    @classmethod
    def get_export_csv_picker(cls) -> FilePicker:
        """Return the lazily created CSV export file picker.

        Returns:
            The shared picker instance for export operations.
        """
        if cls._export_picker_csv is None:
            cls._export_picker_csv = FilePicker()
        return cls._export_picker_csv

    @classmethod
    def init_tts(cls, page: Page, *, service: TtsService | None = None, player=None) -> None:
        """Create the session TTS service.

        Call once from ``main`` after ``set_page``. The ``Audio`` player is
        created during ``speak`` with a non-empty ``src`` already set, because
        Flutter's AudioService throws if it is inited without ``src``.
        Screens should use ``get_tts_service`` or ``speak`` rather than
        constructing ``Audio`` or ``GttsProvider``.

        Args:
            page: Active Flet page; used when ``speak`` mounts the player.
            service: Optional pre-built TTS service (tests).
            player: Optional pre-built player (tests). When omitted, Audio is
                created later in ``speak``.
        """
        from learning_app.tts import GttsProvider, TtsService

        cls._tts_service = service if service is not None else TtsService(GttsProvider())
        if player is None:
            cls._tts_player = None
            cls._tts_retain = []
        else:
            player.on_state_change = cls._on_audio_state_change
            cls._tts_player = player
            cls._retain_tts_player(player)
        cls._tts_mounted = False

    @classmethod
    def get_tts_service(cls) -> TtsService:
        """Return the shared TTS service for this app session.

        Returns:
            The session ``TtsService``.

        Raises:
            AssertionError: If ``init_tts`` has not been called.
        """
        assert cls._tts_service is not None, "TTS service is not initialized"
        return cls._tts_service

    @classmethod
    def get_tts_player(cls) -> fta.Audio:
        """Return the shared Flet Audio player for pronunciations.

        Returns:
            The session ``Audio`` service.

        Raises:
            AssertionError: If ``init_tts`` has not been called, or no
                ``speak`` has created the player yet.
        """
        assert cls._tts_player is not None, "TTS player is not initialized"
        return cls._tts_player

    @classmethod
    def _retain_tts_player(cls, player) -> None:
        """Hold extra Python refs so Flet does not unregister the Dart Audio.

        After each event Flet drops services whose ``getrefcount`` is ``<= 4``
        (Python < 3.14). ``page.services`` is the root view list, so replacing
        ``page.views`` removes that ref and the player is disposed.
        """
        cls._tts_retain = [player, player]

    @classmethod
    def _create_tts_player(cls, src=None) -> fta.Audio:
        return fta.Audio(
            src=src,
            autoplay=True,
            volume=1.0,
            release_mode=fta.ReleaseMode.STOP,
            on_state_change=cls._on_audio_state_change,
            on_loaded=cls._on_audio_loaded,
        )

    @staticmethod
    def _audio_src_from_path(path) -> str:
        """Return a local path Dart ``File.existsSync`` will treat as a file.

        ``file://`` URIs are treated as remote URLs (scheme length > 1), so
        audioplayers calls ``setSourceUrl`` and ``play()`` hangs.
        """
        return str(path.resolve()).replace("\\", "/")

    @classmethod
    def _mount_player(cls, src):
        """Mount Audio with a non-empty src, or push a new src to the live player.

        Flutter's AudioService.update() raises if src is empty, so the player
        must not be added to ``page.services`` until src is set. After
        ``page.views`` replacement the Dart binding is dead and a new Audio
        with src is created.
        """
        page = cls.get_page()
        player = cls._tts_player

        if player is not None and not isinstance(player, fta.Audio):
            player.src = src
            if player not in page.services:
                page.services.append(player)
            return player

        if player is not None and player in page.services:
            player.src = src
            player.autoplay = True
            player.update()
            return player

        if cls._tts_mounted or player is None:
            player = cls._create_tts_player(src=src)
        else:
            player.src = src
            player.autoplay = True
        page.services.append(player)
        cls._tts_player = player
        cls._retain_tts_player(player)
        cls._tts_mounted = True
        update = getattr(page, "update", None)
        if callable(update):
            page.update()
        return player

    @classmethod
    def _can_replay_src(cls, src: str) -> bool:
        """Return True when the live player already has ``src`` loaded.

        Re-assigning the same path does not fire ``on_loaded`` again, so
        ``speak`` would wait the full load timeout before ``play``.
        """
        player = cls._tts_player
        if player is None or getattr(player, "src", None) != src:
            return False
        page = cls.get_page()
        services = getattr(page, "services", None)
        return services is not None and player in services

    @classmethod
    async def speak(cls, text: str, language: str) -> None:
        """Synthesize ``text`` if needed and play every slash-separated member.

        A newer ``speak`` takes over the remaining playlist so two calls do
        not drive ``play`` in parallel. The current clip is not paused or
        stopped. Repeating the same cached file skips remounting and the
        load wait so the speaker button can replay immediately. Screens
        should call this instead of driving ``Audio``.

        Args:
            text: Cell value, possibly containing ``/``.
            language: IETF language tag passed to the TTS provider.
        """
        paths = await cls.get_tts_service().resolve_paths(text, language)
        cls._speak_generation += 1
        generation = cls._speak_generation
        if cls._playback_done is not None and not cls._playback_done.is_set():
            cls._playback_done.set()

        for path in paths:
            if generation != cls._speak_generation:
                return
            done = asyncio.Event()
            cls._playback_done = done
            src = cls._audio_src_from_path(path)
            if cls._can_replay_src(src):
                player = cls._tts_player
            else:
                cls._src_loaded = asyncio.Event()
                player = cls._mount_player(src)
                if isinstance(player, fta.Audio):
                    try:
                        await asyncio.wait_for(cls._src_loaded.wait(), timeout=2)
                    except TimeoutError:
                        pass
            if done.is_set():
                continue
            await player.play()
            try:
                await asyncio.wait_for(done.wait(), timeout=15)
            except TimeoutError:
                pass

    @classmethod
    def _on_audio_loaded(cls, e) -> None:
        event = cls._src_loaded
        if event is not None and not event.is_set():
            event.set()

    @classmethod
    def _on_audio_state_change(cls, e) -> None:
        if getattr(e, "state", None) != fta.AudioState.COMPLETED:
            return
        event = cls._playback_done
        if event is not None and not event.is_set():
            event.set()

    @classmethod
    def disable_all_navigation_controls(cls):
        """Disable available shell navigation controls and update the page.

        Bottom app-bar icon buttons, the floating action button, the
        registered drawer, and home/export sort dropdowns are disabled when
        present.

        Raises:
            AssertionError: If a page has not been registered.
        """
        page = cls.get_page()

        if page.bottom_appbar and page.bottom_appbar.content:
            for control in page.bottom_appbar.content.controls:
                if isinstance(control, IconButton):
                    control.disabled = True

        if page.floating_action_button:
            page.floating_action_button.disabled = True

        if AppChrome.has_drawer():
            AppChrome.get_drawer().disabled = True

        cls._set_tile_sort_enabled(False)
        cls._navigation_disabled = True
        page.update()

    @classmethod
    def enable_all_navigation_controls(cls):
        """Enable available shell navigation controls and update the page.

        Raises:
            AssertionError: If a page has not been registered.
        """
        page = cls.get_page()

        if page.bottom_appbar and page.bottom_appbar.content:
            for control in page.bottom_appbar.content.controls:
                if isinstance(control, IconButton):
                    control.disabled = False

        if page.floating_action_button:
            page.floating_action_button.disabled = False

        if AppChrome.has_drawer():
            AppChrome.get_drawer().disabled = False

        cls._set_tile_sort_enabled(True)
        cls._navigation_disabled = False
        page.update()

    @classmethod
    def is_navigation_disabled(cls) -> bool:
        """Return the navigation state last set by this session registry.

        Returns:
            ``True`` after navigation controls have been disabled and before
            they are enabled again.
        """
        return cls._navigation_disabled

    @classmethod
    def _set_tile_sort_enabled(cls, enabled: bool) -> None:
        from learning_app.ui.body_registry import BodyRegistry

        if BodyRegistry.has_home():
            BodyRegistry.get_home().set_sort_controls_enabled(enabled)
        if BodyRegistry.has_export():
            BodyRegistry.get_export().set_sort_controls_enabled(enabled)
