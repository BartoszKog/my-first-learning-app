import os
import platform
import shutil

class FilePathManager:
    """Class managing file paths in the application"""
    
    # Initialization on first class import
    _data_dir = os.getenv("FLET_APP_STORAGE_DATA")
    _temp_dir = os.getenv("FLET_APP_STORAGE_TEMP")
    _initialized = False
    
    @classmethod
    def initialize(cls):
        """Initialize data directories if they don't exist yet"""
        if cls._initialized:
            return
            
        if cls._data_dir:
            # Create directory for CSV files if it doesn't exist
            cls._csv_dir = os.path.join(cls._data_dir, "csv_files")
            os.makedirs(cls._csv_dir, exist_ok=True)
        else:
            # If environment variable is not available (e.g., in web mode),
            # use the current directory
            cls._csv_dir = os.getcwd()
            
        cls._initialized = True
    
    @classmethod
    def get_csv_path(cls, file_name):
        """Returns the full path to a CSV file"""
        cls.initialize()
        # If file_name already contains a full path, return it
        if cls._data_dir and os.path.dirname(file_name) and cls._csv_dir in file_name:
            return file_name
        return os.path.join(cls._csv_dir, os.path.basename(file_name))
    
    @classmethod
    def get_files_data_path(cls):
        """Returns the path to the files.csv file"""
        cls.initialize()
        return os.path.join(cls._csv_dir, "files.csv")
    
    @classmethod
    def get_data_dir(cls):
        """Returns the application data directory"""
        cls.initialize()
        return cls._data_dir
        
    @classmethod
    def get_temp_dir(cls):
        """Returns the application temporary directory"""
        cls.initialize()
        return cls._temp_dir
        
    @classmethod
    def get_csv_dir(cls):
        """Returns the directory for CSV files"""
        cls.initialize()
        return cls._csv_dir
