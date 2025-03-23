import flet as ft
from ContentTile import ContentTile
from AppData import get_file_names_and_titles, delate_set
from constants import FilesColumns
from Greetings import Greetings
from page_functions import create_alert_dialog
from PageProperties import PageProperties
from FilePathManager import FilePathManager
import threading
import time

class TilesContainer(ft.Container):
    def __init__(self, page=None, export_mode=False):
        super().__init__()   
        
        # attributes involved in searching mode
        self.export_mode = export_mode  
        self.tiles_with_patterns = []
        self.last_pattern = ""
        self.index_of_focused_tile = 0
        self.index_of_all_tiles = 0
        self.lock = threading.Lock()
        
        files_and_titles = self.__validate_and_get_files(PageProperties.get_page()) 
        
        lv = ft.ListView(
            expand=True,
            spacing=10,
            controls=[
                ContentTile(
                    entry[FilesColumns.FILE_NAME.value],
                    entry[FilesColumns.TITLE.value],
                    entry[FilesColumns.SUBTITLE.value],
                    parent_container=self,
                    key=entry[FilesColumns.FILE_NAME.value],
                    export_mode=export_mode)
                for entry in files_and_titles
            ]
        )
        
        self.content = lv
        self.padding = 10
        self.width = PageProperties.width * 0.87
        self.height = PageProperties.height * 0.65
        
    def back_to_main_menu(self, e):
        e.page.controls.clear()
        e.page.appbar.visible = True
        e.page.appbar.title.value = Greetings.get_greeting()
        e.page.bottom_appbar.visible = True
        e.page.floating_action_button.visible = True
        e.page.padding = PageProperties.padding
        body = PageProperties.get_body()
        e.page.add(body)
        body.scale_height_to_page(e.page, factor=0.65)
        body.reset_indications()
        body.turn_off_searching_mode()
        e.page.update()
        
    def refresh_content(self):
        files_and_titles = self.__validate_and_get_files(PageProperties.get_page())
        self.content.controls.clear()
        for entry in files_and_titles:
            self.content.controls.append(
                ContentTile(
                    entry[FilesColumns.FILE_NAME.value], 
                    entry[FilesColumns.TITLE.value],
                    entry[FilesColumns.SUBTITLE.value],
                    parent_container=self,
                    key=entry[FilesColumns.FILE_NAME.value],
                    export_mode=self.export_mode
                )
            )
        self.update()
        
    def did_mount(self):
        # update tiles when control is mounted
        self.refresh_content()
        
    def scale_height_to_page(self, page, factor=0.65):
        self.width = PageProperties.width * 0.87 # 0.87 is the same as in __init__
        self.height = PageProperties.height * factor
        self.update()
        
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
        self.__scroll_to_tile(0, "up")
    
    def turn_off_searching_mode(self):
        # clear all tiles from tiles with patterns and without patterns
        self.tiles_with_patterns.clear()
        
        self.last_pattern = ""
        self.index_of_focused_tile = 0
        self.index_of_all_tiles = 0
        
    def reset_indications(self):
        with self.lock:
            # all tiles
            for tile in self.content.controls:
                tile.reset_indication()
        
    def indicate_patterns_and_scroll_to_first(self, pattern: str):
        with self.lock:
            # check if not last pattern is in the beginning of the new pattern
            if not pattern.lower().startswith(self.last_pattern.lower()):
                # reset tiles with patterns
                for tile in self.tiles_with_patterns:
                    tile.reset_indication()
                
                # clear tiles without patterns and add all tiles to tiles with patterns
                self.tiles_with_patterns.clear()
                self.tiles_with_patterns = self.content.controls.copy()
                self.index_of_focused_tile = 0
                

            new_tiles_with_patterns = []

            for tile in self.tiles_with_patterns:
                if tile.contains_pattern(pattern):
                    if pattern != "":
                        tile.indicate_pattern(pattern)

                    new_tiles_with_patterns.append(tile)
                else:
                    tile.reset_indication()

            self.tiles_with_patterns = new_tiles_with_patterns
            
            # scroll to the first tile with pattern
            if len(self.tiles_with_patterns) > 0:
                if self.index_of_all_tiles - self.__index_of_first_tile_with_pattern(pattern) > 0:
                    self.__scroll_to_tile(0, "up")
                else:
                    self.__scroll_to_tile(0, "down")
                
                if pattern != "": # from all indicated tiles, set main color in the first one
                    self.tiles_with_patterns[0].indicate_pattern(pattern, main_color=True)
                self.index_of_focused_tile = 0
            
            self.last_pattern = pattern
        
    def __index_of_first_tile_with_pattern(self, pattern):
        if pattern == "":
            return 0
        
        for tile in self.content.controls:
            if tile.contains_pattern(pattern):
                return self.content.controls.index(tile)
    
    def __reset_main_color_indication_in_previous_tile(self, index):
        assert index >= 0 and index < len(self.tiles_with_patterns)
        self.tiles_with_patterns[index].indicate_pattern(self.last_pattern, main_color=False)  
            
    def __set_main_color_indication_in_next_tile(self, index):
        assert index < len(self.tiles_with_patterns) and index >= 0
        self.tiles_with_patterns[index].indicate_pattern(self.last_pattern, main_color=True) 
        
    def __scroll_to_tile(self, index, up_or_down): # add argument up_or_down
        assert index < len(self.tiles_with_patterns) and index >= 0
        assert up_or_down == "up" or up_or_down == "down"
        
        DURATION = 0.01
        
        if up_or_down == "down":
            self.index_of_all_tiles = 0
            for tile in self.content.controls:
                if tile.key == self.tiles_with_patterns[index].key:
                    break
                
                time.sleep(DURATION)
                self.content.scroll_to(key = tile.key)
                self.index_of_all_tiles += 1
                
        elif up_or_down == "up":
            break_flag = False                
            self.index_of_all_tiles = len(self.content.controls) - 1
            for tile in reversed(self.content.controls):
                if self.index_of_all_tiles < 0:
                    raise IndexError             
                
                time.sleep(DURATION)
                self.content.scroll_to(key = tile.key)
                if break_flag:
                    break
                
                self.index_of_all_tiles -= 1
                
                if tile.key == self.tiles_with_patterns[index].key:
                    self.index_of_all_tiles += 1
                    break_flag = True             
        
    
    def scroll_to_next(self):
        with self.lock:
            if (self.index_of_focused_tile < len(self.tiles_with_patterns) - 1) and (self.last_pattern != ""):
                self.index_of_focused_tile += 1
                self.__reset_main_color_indication_in_previous_tile(self.index_of_focused_tile - 1)
                self.__set_main_color_indication_in_next_tile(self.index_of_focused_tile)
                self.__scroll_to_tile(self.index_of_focused_tile, "down")
    
    def scroll_to_previous(self):
        with self.lock:
            if (self.index_of_focused_tile > 0) and (self.last_pattern != ""):
                self.index_of_focused_tile -= 1
                self.__reset_main_color_indication_in_previous_tile(self.index_of_focused_tile+1)
                self.__set_main_color_indication_in_next_tile(self.index_of_focused_tile)
                self.__scroll_to_tile(self.index_of_focused_tile, "up")

