import flet as ft
from ContentTile import ContentTile
from AppData import get_file_names_and_titles, delate_set
from constants import FilesColumns
from Greetings import Greetings
from page_functions import create_alert_dialog
from PageProperties import PageProperties
from FilePathManager import FilePathManager
import asyncio
import threading

class TilesContainer(ft.Container):
    WIDTH_FACTOR = 0.87
    HEIGHT_FACTOR = 0.85
    DEFAULT_APPBAR_HEIGHT = 100
    DEFAULT_BOTTOM_APPBAR_HEIGHT = 80
    SCROLL_PIXELS_PER_TILE = 69
    SCROLL_OFFSET_CORRECTION = -130

    def __init__(self, page=None, export_mode=False):
        super().__init__()   
        
        # attributes involved in searching mode
        self.export_mode = export_mode  
        self.tiles_with_patterns = []
        self.last_pattern = ""
        self.index_of_focused_tile = 0
        self.index_of_all_tiles = 0
        self.lock = threading.Lock()
        
        self.files_and_titles = self.__validate_and_get_files(PageProperties.get_page()) 
        
        lv = ft.ListView(
            expand=True,
            spacing=10,
            controls=[
                self.__create_content_tile(entry)
                for entry in self.files_and_titles
            ]
        )
        
        self.content = lv
        self.padding = 10
        self.__sync_size_to_page(page)
        
    @staticmethod
    def back_to_main_menu(e):
        page = e.page
        page.controls.clear()
        page.appbar.visible = True
        page.appbar.title.value = Greetings.get_greeting()
        page.bottom_appbar.visible = True
        page.floating_action_button.visible = True
        page.padding = PageProperties.padding
        PageProperties.set_width_height_from_page(page)
        body = TilesContainer(page)
        PageProperties.set_body(body)
        page.add(body)
        
    def refresh_content(self):
        self.files_and_titles = self.__validate_and_get_files(PageProperties.get_page())
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
        # update tiles when control is mounted
        self.__sync_size_to_page(self.page or PageProperties.get_page())
        self.refresh_content()
        
    def scale_height_to_page(self, page, factor=0.65):
        self.width = self.__get_layout_width(page) * self.WIDTH_FACTOR
        self.height = self.__get_available_height(page) * factor
        self.update()

    def __sync_size_to_page(self, page=None):
        if page is not None:
            PageProperties.set_width_height_from_page(page)
        self.width = self.__get_layout_width(page) * self.WIDTH_FACTOR
        self.height = self.__get_available_height(page) * self.HEIGHT_FACTOR

    def __get_layout_width(self, page=None):
        if page is not None and page.width:
            return page.width
        if page is not None and getattr(page, "window", None) and page.window.width:
            return page.window.width
        return PageProperties.width

    def __get_available_height(self, page=None):
        if page is None:
            return PageProperties.height

        window_height = page.window.height if getattr(page, "window", None) and page.window.height else page.height
        if not window_height:
            return PageProperties.height

        occupied_height = 0
        if page.appbar and getattr(page.appbar, "visible", True):
            occupied_height += (
                getattr(page.appbar, "toolbar_height", None)
                or getattr(page.appbar, "height", None)
                or self.DEFAULT_APPBAR_HEIGHT
            )
        if page.bottom_appbar and getattr(page.bottom_appbar, "visible", True):
            occupied_height += getattr(page.bottom_appbar, "height", None) or self.DEFAULT_BOTTOM_APPBAR_HEIGHT

        padding = page.padding
        if padding:
            occupied_height += (padding.top or 0) + (padding.bottom or 0)

        return max(window_height - occupied_height, 0)
        
    def has_content_tiles(self):
        """
        Check if the container has any ContentTile controls
        """
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
        """
        Validates files.csv and handles the repair process.
        Returns a list of files to be displayed as tiles.
        """
        # Check validity of files.csv
        from CSVProcessor import CSVProcessor
        files_validation = CSVProcessor.validate_files_csv()
        
        # If the file doesn't exist or has errors, show dialog and disable navigation
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
                # Disable all navigation controls
                PageProperties.disable_all_navigation_controls()
                
                create_alert_dialog(
                    page=page,
                    title="Configuration File Issues",
                    content=error_message,
                    close_button_text="No",
                    action_button_text="Yes, repair",
                    action_function=lambda e: self.__repair_files_and_reload(e)
                )
                # Return empty list - content will be updated after repair
                return []
        
        # Get list of files
        files_and_titles = get_file_names_and_titles()
        
        # Check if files physically exist
        file_has_been_removed = False
        files_to_remove = []
        
        for entry in files_and_titles:
            if not self.__file_exist(entry[FilesColumns.FILE_NAME.value]):
                if page is not None:
                    create_alert_dialog(
                        page=page,
                        title="File not found",
                        content=f"File {entry[FilesColumns.FILE_NAME.value]} was not found. \nIt has been removed from the list.",
                        close_button_text="OK"
                    )
                files_to_remove.append(entry[FilesColumns.FILE_NAME.value])
                file_has_been_removed = True
        
        # Remove files that don't physically exist
        for file_name in files_to_remove:
            delate_set(file_name, file_not_exist=True)
        
        if file_has_been_removed:
            files_and_titles = get_file_names_and_titles()
        
        return files_and_titles

    def __repair_files_and_reload(self, e):
        """
        Repairs files.csv and updates the view.
        """
        from CSVProcessor import CSVProcessor
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
                close_button_text="OK"
            )

    def __on_repair_success(self, e = None):
        """
        Handles successful repair of files.csv
        """
        # Re-enable navigation controls
        PageProperties.enable_all_navigation_controls()
        # Refresh content to load repaired data
        self.refresh_content()  
    
    # Methods involved in searching mode
    def trigger_searching_mode(self):
        # add all tiles to tiles with patterns
        self.tiles_with_patterns = self.content.controls.copy()
        self.index_of_all_tiles = len(self.content.controls) - 1 # it is used in __scroll_to_tile method
        if len(self.tiles_with_patterns) > 0:
            self.__scroll_to_tile(0, "up")
    
    def turn_off_searching_mode(self):
        # clear all tiles from tiles with patterns and without patterns
        self.tiles_with_patterns.clear()
        
        self.last_pattern = ""
        self.index_of_focused_tile = 0
        self.index_of_all_tiles = 0
        
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
            
            # scroll to the first tile with pattern
            if len(self.tiles_with_patterns) > 0:
                self.__scroll_to_tile(0, "up")
                self.index_of_focused_tile = 0
            
            self.last_pattern = pattern
        
    async def __scroll_to_offset(self, offset):
        await self.content.scroll_to(offset=offset)

    def __schedule_scroll_to_offset(self, offset):
        page = self.page or PageProperties.get_page()
        if hasattr(page, "run_task"):
            page.run_task(self.__scroll_to_offset, offset)
        else:
            asyncio.create_task(self.__scroll_to_offset(offset))
        
    def __scroll_to_tile(self, index, up_or_down): # add argument up_or_down
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

