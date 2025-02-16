import flet as ft

def quit_main_menu(e):
    e.page.controls.clear()
    e.page.appbar.visible = False
    e.page.bottom_appbar.visible = False
    e.page.floating_action_button.visible = False
    e.page.update()
    
def create_alert_dialog(page, title, content, close_button_text="OK", action_button_text=None, action_function=None):
    def close_action(e):
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