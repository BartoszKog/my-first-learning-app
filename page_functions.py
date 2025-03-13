import flet as ft

def quit_main_menu(e):
    e.page.controls.clear()
    e.page.appbar.visible = False
    e.page.bottom_appbar.visible = False
    e.page.floating_action_button.visible = False
    e.page.update()
    
def create_alert_dialog(page, title, content, close_button_text="OK", action_button_text=None, action_function=None, close_action_function=None):
    """
    Creates and displays an alert dialog using the Flet library.
    This function creates a customizable alert dialog with a title, content, and action buttons.
    The dialog is added to the page's overlay and displayed immediately.
    Parameters:
        page (ft.Page): The page where the dialog should be displayed.
        title (str): The title text of the alert dialog.
        content (str): The main content text of the alert dialog.
        close_button_text (str, optional): The text for the close button. Defaults to "OK".
        action_button_text (str, optional): The text for the optional action button. Required if action_function is provided.
        action_function (callable, optional): A function to be called when the action button is clicked.
                                             Should accept an event parameter.
        close_action_function (callable, optional): A function to be called when the close button is clicked,
                                                   before the dialog is closed. Should accept an event parameter.
    Returns:
        None: The function displays the dialog but doesn't return any value.
    Note:
        This function automatically handles adding the dialog to the page overlay and removing it
        when either button is clicked.
    """
    def close_action(e):
        if close_action_function:
            close_action_function(e)
        e.page.close(alert_dialog)
        e.page.overlay.remove(alert_dialog) # Remove the dialog from the overlay
        
    actions = [ft.TextButton(close_button_text, on_click=close_action)]
    
    if action_function:
        def action(e):
            action_function(e)
            e.page.close(alert_dialog)
            e.page.overlay.remove(alert_dialog)
        
        actions.append(ft.TextButton(action_button_text, on_click=action))
    
    alert_dialog = ft.AlertDialog(
        title=ft.Text(title),
        content=ft.Text(content),
        actions=actions,
        actions_alignment=ft.MainAxisAlignment.END,
    )
    
    page.overlay.append(alert_dialog)
    alert_dialog.open = True
    page.update()
    
def is_instance_in_the_page(page, instance):
    for control in page.controls:
        if isinstance(control, instance):
            return True
    return False

def set_theme_from_bgcolor(page, bgcolor):
    page.bgcolor = bgcolor
    # here we can implement more options for setting theme