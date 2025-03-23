import flet as ft
import time
from page_functions import create_alert_dialog

def ensure_valid_dimensions(page: ft.Page):
    """
    Ensures that page dimensions are valid (not zero or close to zero) on Android devices.
    If dimensions are invalid, tries to recover from client_storage or show alert.
    
    Args:
        page: The flet Page object
    Returns:
        tuple: (width, height) with valid dimensions or None if using page defaults
    """
    # Only run on Android platform
    if page.platform != ft.PagePlatform.ANDROID:
        return None, None
    
    # Define minimum acceptable dimensions
    MIN_DIMENSION = 10
    MAX_RETRY = 30  # Number of retries (roughly equivalent to 3 seconds)
    
    # Helper function to check and save dimensions
    def _check_and_save_dimensions():
        if page.width >= MIN_DIMENSION and page.height >= MIN_DIMENSION:
            # Valid dimensions found, save them for future use
            page.client_storage.set("saved_page_width", page.width)
            page.client_storage.set("saved_page_height", page.height)
            return True
        return False
    
    # First check if dimensions are valid immediately
    if _check_and_save_dimensions():
        return None, None  # Return None to use page dimensions directly
    
    # Try a few quick updates to see if dimensions become available
    for _ in range(MAX_RETRY):
        page.update()
        time.sleep(0.1)  # Short delay between updates
        
        if _check_and_save_dimensions():
            return None, None  # Return None to use page dimensions directly
    
    # If we still don't have valid dimensions, check if we have saved values
    if page.client_storage.contains_key("saved_page_width") and page.client_storage.contains_key("saved_page_height"):
        saved_width = page.client_storage.get("saved_page_width")
        saved_height = page.client_storage.get("saved_page_height")
        
        if saved_width >= MIN_DIMENSION and saved_height >= MIN_DIMENSION:
            return saved_width, saved_height
    
    # If we still don't have valid dimensions, show an alert
    create_alert_dialog(
        page, 
        "Screen Size Issue", 
        "Unable to detect proper screen dimensions. Please rotate your device to change orientation, then rotate back. If you will not do it, application layout might be incorrect."
    )
    
    # Initialize values if they don't exist
    if not page.client_storage.contains_key("saved_page_width"):
        # Use device-agnostic values that will be overridden once we get valid dimensions
        page.client_storage.set("saved_page_width", 360)  # Common mobile width
        page.client_storage.set("saved_page_height", 640)  # Common mobile height
        return 360, 640
    else:
        # Return the saved values even if they're not ideal
        return page.client_storage.get("saved_page_width"), page.client_storage.get("saved_page_height")
