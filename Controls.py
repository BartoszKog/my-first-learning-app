import flet as ft
from PageProperties import PageProperties

class WordField(ft.TextField):
    def __init__(self, label: str, width: int = 250, read_only: bool = True, autofocus = False):
        super().__init__()
        self.label = label
        self.width = width
        self.read_only = read_only
        self.width_border_indicator = 1
        
        if autofocus:
            self.autofocus = True
        
    def set_value(self, value: str):
        self.value = value
        self.update()
        
    def get_value(self):
        return self.value
    
    def set_green_border(self):
        self.border_color = ft.colors.GREEN
        self.border_width = self.width_border_indicator
        self.update()
        
    def set_red_border(self):
        self.border_color = ft.colors.RED
        self.border_width = self.width_border_indicator
        self.update()
        
    def reset(self):
        self.border_color = ft.colors.BLACK
        self.value = ""
        self.disabled = False
        self.read_only = False
        self.border_width = 1
        self.update()
        
    def disable(self):
        self.disabled = True
        self.update()
        
    def make_read_only(self):
        self.read_only = True
        self.update()
        
    def contain_word(self, word: str):
        # Checks if the word field contains the word.
        splitted_word = word.split("/") if "/" in word else [word]
        
        return self.get_value().strip() in splitted_word
    
    def indicate_good_answer(self, word: str):
        self.set_green_border()
        self.make_read_only()
        self.set_value(word)
        
    def indicate_bad_answer(self, word: str):
        self.set_red_border()
        self.make_read_only()
        self.set_value(word)
        
    def did_mount(self):
        # Set border width, based on the theme mode.
        if PageProperties.dark_mode:
            self.width_border_indicator = 1
        else:
            self.width_border_indicator = 3
        

class ProgressBar(ft.Column):
    def __init__(self, qty: int = 10, start: int = 0, width: int = 250, word: str = "Answered", div_qty: int = 1):
        super().__init__()
        assert start <= qty, "The start quantity must be less than or equal to the maximum quantity."
        assert start >= 0, "The start quantity must be greater than or equal to zero."
        assert qty > 0, "The maximum quantity must be greater than zero."
        assert (div_qty >= 1) and (div_qty <= qty), "The division quantity must be greater than or equal to one and less than or equal to the maximum quantity."
        
        self.current_qty = start
        self.max_qty = qty
        self.word = word
        self.div_qty = div_qty
        self.word = word
        if div_qty == 1:
            self.text = ft.Text(f"{word}: {self.current_qty}/{self.max_qty}")
        else: # float display
            self.text = ft.Text(f"{word}: {self.current_qty/div_qty:.2f}/{self.max_qty/div_qty:.0f}")
        
        self.pb = ft.ProgressBar(value=self.current_qty / self.max_qty, 
                                 width=width, 
                                 color=ft.colors.ORANGE_ACCENT,
                                 bgcolor=ft.colors.BLACK)
        self.controls = [self.text, self.pb]
    
    def __change_text(self):
        if self.div_qty == 1:
            self.text.value = f"{self.word}: {self.current_qty}/{self.max_qty}"
        else: # float display
            numerator = self.current_qty / self.div_qty
            denominator = self.max_qty / self.div_qty
            formatted_numerator = f"{numerator:.2f}".rstrip('0').rstrip('.') # remove trailing zeros and dot
            formatted_denominator = f"{denominator:.0f}"
            self.text.value = f"{self.word}: {formatted_numerator}/{formatted_denominator}"
    
    def increase(self):
        self.current_qty += 1
        if self.current_qty > self.max_qty:
            raise Exception( \
                "The current quantity is greater than the maximum quantity.")
            
        # self.text.value = f"{self.word}: {self.current_qty}/{self.max_qty}"
        self.__change_text()
        self.pb.value = self.current_qty / self.max_qty
        self.update()
        
    def increase_by(self, qty: int):
        self.current_qty += qty
        if self.current_qty > self.max_qty:
            raise Exception( \
                "The current quantity is greater than the maximum quantity.")
            
        # self.text.value = f"{self.word}: {self.current_qty}/{self.max_qty}"
        self.__change_text()
        self.pb.value = self.current_qty / self.max_qty
        self.update()
        
    def set_max_qty(self, qty: int):
        self.max_qty = qty
        # self.text.value = f"{self.word}: {self.current_qty}/{self.max_qty}"
        self.__change_text()
        self.pb.value = self.current_qty / self.max_qty
        self.update()
        
    def reset(self):
        self.current_qty = 0
        # self.text.value = f"{self.word}: {self.current_qty}/{self.max_qty}"
        self.__change_text()
        self.pb.value = self.current_qty / self.max_qty
        self.update()
        
    def set_certain_qty(self, qty):
        assert qty <= self.max_qty, "The quantity must be less than or equal to the maximum quantity."
        self.current_qty = qty
        self.__change_text()
        self.pb.value = self.current_qty / self.max_qty
        self.update()
        