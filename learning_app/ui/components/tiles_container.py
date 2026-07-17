import asyncio
import threading

import flet as ft

from learning_app.data.app_data import delate_set, get_file_names_and_titles
from learning_app.data.constants import FilesColumns
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
    with ``BodyRegistry`` when the container is shared across routes.

    Args:
        page: Optional page used to refresh layout metrics on construction.
        export_mode: When ``True``, tiles use export-oriented actions.
    """

    SCROLL_PIXELS_PER_TILE = 95
    SCROLL_OFFSET_CORRECTION = -100

    def __init__(self, page=None, export_mode=False):
        super().__init__()

        self.export_mode = export_mode
        self.tiles_with_patterns = []
        self.last_pattern = ""
        self.index_of_focused_tile = 0
        self.index_of_all_tiles = 0
        self.lock = threading.Lock()

        self.files_and_titles = self.__validate_and_get_files(AppSession.get_page())

        lv = ft.ListView(
            expand=True,
            spacing=10,
            controls=[
                self.__create_content_tile(entry)
                for entry in self.files_and_titles
            ],
        )

        self.content = lv
        self.padding = 10
        self.expand = True
        if page is not None:
            self.apply_flex_layout(LayoutMetricsStore.refresh(page))

    def refresh_content(self):
        self.files_and_titles = self.__validate_and_get_files(AppSession.get_page())
        self.content.controls.clear()
        for entry in self.files_and_titles:
            self.content.controls.append(self.__create_content_tile(entry))
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
        self.content.controls.clear()
        for entry in self.files_and_titles:
            self.content.controls.append(self.__create_content_tile(entry, pattern, main_key))
        self.update()

    def did_mount(self):
        page = self.page or AppSession.get_page()
        self.apply_flex_layout(LayoutMetricsStore.refresh(page))
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
        return len(self.content.controls) > 0

    @staticmethod
    def __file_exist(file_name):
        file_path = FilePathManager.get_csv_path(file_name)
        try:
            with open(file_path):
                return True
        except FileNotFoundError:
            return False

    def __validate_and_get_files(self, page=None):
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

            if page is not None:
                AppSession.disable_all_navigation_controls()

                create_alert_dialog(
                    page=page,
                    title="Configuration File Issues",
                    content=error_message,
                    close_button_text="No",
                    action_button_text="Yes, repair",
                    action_function=lambda e: self.__repair_files_and_reload(e),
                )
                return []

        files_and_titles = get_file_names_and_titles()

        file_has_been_removed = False
        files_to_remove = []

        for entry in files_and_titles:
            if not self.__file_exist(entry[FilesColumns.FILE_NAME.value]):
                if page is not None:
                    create_alert_dialog(
                        page=page,
                        title="File not found",
                        content=f"File {entry[FilesColumns.FILE_NAME.value]} was not found. \nIt has been removed from the list.",
                        close_button_text="OK",
                    )
                files_to_remove.append(entry[FilesColumns.FILE_NAME.value])
                file_has_been_removed = True

        for file_name in files_to_remove:
            delate_set(file_name, file_not_exist=True)
            if page is not None:
                from learning_app.ui.router import remove_views_for_set_file

                remove_views_for_set_file(page, file_name)

        if file_has_been_removed:
            files_and_titles = get_file_names_and_titles()

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
        self.tiles_with_patterns = self.content.controls.copy()
        self.index_of_all_tiles = len(self.content.controls) - 1
        if len(self.tiles_with_patterns) > 0:
            self.__scroll_to_tile(0, "up")

    def turn_off_searching_mode(self):
        with self.lock:
            self.tiles_with_patterns.clear()
            self.last_pattern = ""
            self.index_of_focused_tile = 0
            self.index_of_all_tiles = 0
            self.__reload_tiles()

    def reset_indications(self):
        with self.lock:
            self.__reload_tiles()
            self.tiles_with_patterns = self.content.controls.copy()

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
                tile for tile in self.content.controls
                if tile.key in matching_keys
            ]

            if len(self.tiles_with_patterns) > 0:
                self.__scroll_to_tile(0, "up")
                self.index_of_focused_tile = 0

            self.last_pattern = pattern

    async def __scroll_to_offset(self, offset):
        await self.content.scroll_to(offset=offset)

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
        for tile_index, tile in enumerate(self.content.controls):
            if tile.key == target_key:
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
                    tile for tile in self.content.controls
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
                    tile for tile in self.content.controls
                    if tile.contains_pattern(self.last_pattern)
                ]
                self.__scroll_to_tile(self.index_of_focused_tile, "up")
