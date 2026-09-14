import asyncio
import os
import threading

import flet as ft

from learning_app.data.app_data import delate_set, get_file_names_and_titles
from learning_app.data.constants import FilesColumns, SetSortMode
from learning_app.data.file_path_manager import FilePathManager
from learning_app.ui.components.content_tile import ContentTile
from learning_app.ui.layout_host import control_is_on_page
from learning_app.ui.layout_metrics import LayoutMetrics, LayoutMetricsStore
from learning_app.ui.page_functions import create_alert_dialog
from learning_app.ui.app_session import AppSession


class TilesContainer(ft.Container):
    """Scrollable list of learning-set tiles for Home or export mode.

    Loads catalog entries, builds ``ContentTile`` children, and supports
    search filtering used by ``SearchControl``. Register Home/export instances
    with ``BodyRegistry`` when the container is shared (Home, export, and
    in-place search).

    Args:
        page: Optional page used to refresh layout metrics on construction.
        export_mode: When ``True``, tiles use export-oriented actions.
    """

    SCROLL_PIXELS_PER_TILE = 100
    SCROLL_OFFSET_CORRECTION = -100
    _shared_sort_mode: SetSortMode = SetSortMode.LAST_USED

    @classmethod
    def get_shared_sort_mode(cls) -> SetSortMode:
        return cls._shared_sort_mode

    @classmethod
    def set_shared_sort_mode(cls, mode: SetSortMode) -> None:
        """Update the in-memory sort mode shared for this app session."""
        cls._shared_sort_mode = mode

    def __create_sort_dropdown(self) -> ft.Dropdown:
        return ft.Dropdown(
            value=self.sort_mode.value,
            options=[
                ft.DropdownOption(key=SetSortMode.LAST_USED.value, text="Sort by last used"),
                ft.DropdownOption(key=SetSortMode.CREATED.value, text="Sort by date created"),
                ft.DropdownOption(key=SetSortMode.TITLE.value, text="Sort alphabetically (A-Z)"),
                ft.DropdownOption(key=SetSortMode.USE_COUNT.value, text="Sort by most used"),
            ],
            on_select=self.__on_sort_change,
            text_size=14,
            dense=True,
            filled=True,
            expand=True,
            # fill_color = closed field (blend with Card); bgcolor = open menu panel
            fill_color=ft.Colors.TRANSPARENT,
            bgcolor=ft.Colors.SURFACE,
            border_color=ft.Colors.TRANSPARENT,
            focused_border_color=ft.Colors.TEAL_ACCENT,
            border_radius=10,
            leading_icon=ft.Icons.SORT,
            text_align=ft.TextAlign.CENTER,
            disabled=AppSession.is_navigation_disabled(),
        )

    def __rebuild_sort_bar(self) -> None:
        """Create the sort dropdown in a Card matching ContentTile chrome."""
        self.sort_dropdown = self.__create_sort_dropdown()
        self.sort_bar = ft.Card(
            content=ft.Container(
                content=self.sort_dropdown,
                padding=ft.Padding.symmetric(horizontal=4, vertical=2),
            ),
            margin=5,
        )

    def __init__(self, page=None, export_mode=False):
        super().__init__()

        self.export_mode = export_mode
        self.searching = False
        self.tiles_with_patterns = []
        self.last_pattern = ""
        self.index_of_focused_tile = 0
        self.index_of_all_tiles = 0
        self.lock = threading.Lock()
        self.sort_mode = self.get_shared_sort_mode()
        self.__rebuild_sort_bar()

        self.files_and_titles = self.__validate_and_get_files(AppSession.get_page())
        self._skip_next_mount_refresh = True

        self.list_view = ft.ListView(
            expand=True,
            spacing=10,
            controls=self.__build_list_controls(),
        )

        self.content = self.list_view
        self.padding = 10
        self.expand = True
        if page is not None:
            self.apply_flex_layout(LayoutMetricsStore.refresh(page))

    def __build_list_controls(self, pattern: str = "", main_key=None):
        tiles = [
            self.__create_content_tile(entry, pattern, main_key)
            for entry in self.files_and_titles
        ]
        if self.searching:
            return tiles
        return [self.sort_bar] + tiles

    def __tile_controls(self):
        return [control for control in self.list_view.controls if isinstance(control, ContentTile)]

    def set_sort_controls_enabled(self, enabled: bool) -> None:
        """Enable or disable the sort dropdown used on this tile list."""
        self.sort_dropdown.disabled = not enabled

    def apply_sort_mode(self, mode: SetSortMode, *, reload_from_disk: bool = True) -> None:
        """Apply a sort mode locally and keep the dropdown label in sync."""
        self.sort_mode = mode
        self.sort_dropdown.value = mode.value
        if reload_from_disk:
            page = AppSession.get_page()
            self.files_and_titles = self.__validate_and_get_files(page)
        self.__reload_tiles(self.last_pattern)

    def __on_sort_change(self, e):
        if AppSession.is_navigation_disabled():
            return
        try:
            mode = SetSortMode(e.control.value)
        except ValueError:
            mode = SetSortMode.LAST_USED
        self.set_shared_sort_mode(mode)
        self.apply_sort_mode(mode)
        self.__sync_other_containers(mode)
        e.page.update()

    def __sync_other_containers(self, mode: SetSortMode) -> None:
        from learning_app.ui.body_registry import BodyRegistry

        others = []
        if BodyRegistry.has_home():
            others.append(BodyRegistry.get_home())
        if BodyRegistry.has_export():
            others.append(BodyRegistry.get_export())
        for container in others:
            if container is self:
                continue
            # Home/Export under a replaced drawer route stays in BodyRegistry but
            # is detached; updating it raises "Control must be added to the page".
            if control_is_on_page(container):
                container.apply_sort_mode(mode)

    def refresh_content(self, *, show_alerts=True):
        self.sort_mode = self.get_shared_sort_mode()
        self.files_and_titles = self.__validate_and_get_files(
            AppSession.get_page(),
            show_alerts=show_alerts,
        )
        self.__reload_tiles()
        if control_is_on_page(self):
            self.update()

    def __create_content_tile(self, entry, pattern: str = "", main_key=None):
        key = entry[FilesColumns.FILE_NAME.value]
        title = entry[FilesColumns.TITLE.value]
        matching_pattern = pattern if pattern and pattern.lower() in title.lower() else ""
        return ContentTile(
            key,
            title,
            entry[FilesColumns.SUBTITLE.value],
            parent_container=self,
            key=key,
            export_mode=self.export_mode,
            pattern=matching_pattern,
            main_color=key == main_key,
        )

    def __reload_tiles(self, pattern: str = "", main_key=None):
        self.sort_dropdown.value = self.sort_mode.value
        self.list_view.controls = self.__build_list_controls(pattern, main_key)
        if control_is_on_page(self):
            self.update()

    def did_mount(self):
        page = self.page or AppSession.get_page()
        self.apply_flex_layout(LayoutMetricsStore.refresh(page))
        self.sort_mode = self.get_shared_sort_mode()
        self.sort_dropdown.value = self.sort_mode.value
        # Catalog is already loaded in __init__; skip the first mount refresh
        # so a repair dialog is not stacked on top of itself.
        if self._skip_next_mount_refresh:
            self._skip_next_mount_refresh = False
            return
        self.refresh_content()

    def apply_flex_layout(self, metrics: LayoutMetrics | None = None):
        if metrics is None:
            metrics = LayoutMetricsStore.get()
        self.expand = True
        self.width = metrics.body_width
        self.height = None
        if control_is_on_page(self):
            self.update()

    def has_content_tiles(self):
        return len(self.__tile_controls()) > 0

    @staticmethod
    def __file_exist(file_name):
        file_path = FilePathManager.get_csv_path(file_name)
        try:
            with open(file_path):
                return True
        except FileNotFoundError:
            return False

    def __validate_and_get_files(self, page=None, *, show_alerts=True):
        from learning_app.data.csv_processor import CSVProcessor
        files_validation = CSVProcessor.validate_files_csv()

        if not files_validation["is_valid"] and files_validation["errors"]:
            error_message = "The configuration file files.csv has issues that need to be fixed:\n\n"

            if files_validation["errors"]:
                error_message += "Errors:\n"
                for error in files_validation["errors"]:
                    error_message += f"- {error}\n"

            if files_validation["warnings"]:
                error_message += "\nWarnings:\n"
                for warning in files_validation["warnings"]:
                    error_message += f"- {warning}\n"

            error_message += "\nWould you like to attempt automatic repair? This may remove some invalid entries."

            if page is not None and show_alerts:
                AppSession.disable_all_navigation_controls()
                self.set_sort_controls_enabled(False)

                create_alert_dialog(
                    page=page,
                    title="Configuration File Issues",
                    content=error_message,
                    close_button_text="No",
                    action_button_text="Yes, repair",
                    action_function=lambda e: self.__repair_files_and_reload(e),
                )
            return []

        files_and_titles = get_file_names_and_titles(self.sort_mode)

        files_to_remove = [
            entry[FilesColumns.FILE_NAME.value]
            for entry in files_and_titles
            if not self.__file_exist(entry[FilesColumns.FILE_NAME.value])
        ]

        if files_to_remove:
            if page is not None and show_alerts:
                names = [os.path.basename(name) for name in files_to_remove]
                if len(names) == 1:
                    content = (
                        f"The set file {names[0]} was not found.\n"
                        "It has been removed from the list."
                    )
                else:
                    listed = "\n".join(f"• {name}" for name in names)
                    content = (
                        "These set files were not found and have been removed "
                        f"from the list:\n\n{listed}"
                    )
                create_alert_dialog(
                    page=page,
                    title="File not found",
                    content=content,
                    close_button_text="OK",
                )
            from learning_app.ui.router import remove_views_for_set_file

            for file_name in files_to_remove:
                delate_set(file_name, file_not_exist=True)
                if page is not None:
                    remove_views_for_set_file(page, file_name)

            files_and_titles = get_file_names_and_titles(self.sort_mode)

        return files_and_titles

    def __repair_files_and_reload(self, e):
        from learning_app.data.csv_processor import CSVProcessor
        repair_result = CSVProcessor.repair_files_csv()

        result_message = "Repair results:\n\n"
        for action in repair_result["repair_actions"]:
            result_message += f"- {action}\n"

        if repair_result["success"]:
            self.__on_repair_success(e)
            result_message += "\nConfiguration file has been repaired. The application will now reload."

            create_alert_dialog(
                page=e.page,
                title="Repair completed successfully",
                content=result_message,
                close_button_text="OK",
            )
        else:
            result_message += "\nRepair failed. Please check your configuration file manually."

            create_alert_dialog(
                page=e.page,
                title="Repair failed",
                content=result_message,
                close_button_text="OK",
            )

    def __on_repair_success(self, e=None):
        AppSession.enable_all_navigation_controls()
        self.refresh_content()

    def trigger_searching_mode(self):
        self.searching = True
        self.__reload_tiles(self.last_pattern)
        self.tiles_with_patterns = self.__tile_controls().copy()
        self.index_of_all_tiles = max(len(self.list_view.controls) - 1, 0)
        if len(self.tiles_with_patterns) > 0:
            self.__scroll_to_tile(0, "up")

    def turn_off_searching_mode(self):
        with self.lock:
            self.searching = False
            self.tiles_with_patterns.clear()
            self.last_pattern = ""
            self.index_of_focused_tile = 0
            self.index_of_all_tiles = 0
            self.__reload_tiles()

    def reset_indications(self):
        with self.lock:
            self.__reload_tiles()
            self.tiles_with_patterns = self.__tile_controls().copy()

    def indicate_patterns_and_scroll_to_first(self, pattern: str):
        with self.lock:
            self.index_of_focused_tile = 0
            matching_keys = [
                entry[FilesColumns.FILE_NAME.value]
                for entry in self.files_and_titles
                if pattern.lower() in entry[FilesColumns.TITLE.value].lower()
            ]
            main_key = matching_keys[0] if pattern and matching_keys else None
            self.__reload_tiles(pattern, main_key)
            self.tiles_with_patterns = [
                tile for tile in self.__tile_controls()
                if tile.key in matching_keys
            ]

            if len(self.tiles_with_patterns) > 0:
                self.__scroll_to_tile(0, "up")
                self.index_of_focused_tile = 0

            self.last_pattern = pattern

    async def __scroll_to_offset(self, offset):
        await self.list_view.scroll_to(offset=offset)

    def __schedule_scroll_to_offset(self, offset):
        page = self.page or AppSession.get_page()
        if hasattr(page, "run_task"):
            page.run_task(self.__scroll_to_offset, offset)
        else:
            asyncio.create_task(self.__scroll_to_offset(offset))

    def __scroll_to_tile(self, index, up_or_down):
        assert index < len(self.tiles_with_patterns) and index >= 0
        assert up_or_down == "up" or up_or_down == "down"

        target_key = self.tiles_with_patterns[index].key
        for tile_index, tile in enumerate(self.list_view.controls):
            if isinstance(tile, ContentTile) and tile.key == target_key:
                self.index_of_all_tiles = tile_index
                offset = max(
                    tile_index * self.SCROLL_PIXELS_PER_TILE + self.SCROLL_OFFSET_CORRECTION,
                    0,
                )
                self.__schedule_scroll_to_offset(offset)
                return

        raise IndexError

    def scroll_to_next(self):
        with self.lock:
            if (self.index_of_focused_tile < len(self.tiles_with_patterns) - 1) and (self.last_pattern != ""):
                self.index_of_focused_tile += 1
                main_key = self.tiles_with_patterns[self.index_of_focused_tile].key
                self.__reload_tiles(self.last_pattern, main_key)
                self.tiles_with_patterns = [
                    tile for tile in self.__tile_controls()
                    if tile.contains_pattern(self.last_pattern)
                ]
                self.__scroll_to_tile(self.index_of_focused_tile, "down")

    def scroll_to_previous(self):
        with self.lock:
            if (self.index_of_focused_tile > 0) and (self.last_pattern != ""):
                self.index_of_focused_tile -= 1
                main_key = self.tiles_with_patterns[self.index_of_focused_tile].key
                self.__reload_tiles(self.last_pattern, main_key)
                self.tiles_with_patterns = [
                    tile for tile in self.__tile_controls()
                    if tile.contains_pattern(self.last_pattern)
                ]
                self.__scroll_to_tile(self.index_of_focused_tile, "up")
