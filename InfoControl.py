import flet as ft
from PageProperties import PageProperties
from constants import MAX_ROWS
 
class InfoControl(ft.Container):
    MD_TEXT = f"""
# About the App

This app is designed for effective learning of words and definitions. It allows you to import your own study sets, track your progress, and export data.

# Learning Algorithm

The app utilizes a learning algorithm visualized in the following graph:

![Learning Algorithm](assets/graph.png)

## Word Learning Queue

Words are queued for learning according to the following states:

- **Unknown**: Words that have been verified as unknown.
- **Unverified**: Words that have not yet been verified and are not marked as requiring learning.
- **Unconfirmed that known**: Words that have been marked as correctly answered but have not yet been confirmed as known.
- **Known**: Words that have been correctly answered twice in a row. Once marked as known, they are no longer added to the learning queue.

The process of queuing words for learning is as follows:
1. First, words in the **Unknown** state (0/0/1) are selected.
2. If there are not enough words in the **Unknown** state, words in the **Unverified** state (0/0/0) are added.
3. If there are still not enough words, words in the **Unconfirmed that known** state (1/0/0, 1/0/1, 1/1/1) are added.

### Explanation of State Codes (0/0/0)

The state codes (e.g., 0/0/0) represent the following attributes of a word:
- The first digit indicates whether the word was answered correctly in the last attempt (0 for no, 1 for yes).
- The second digit indicates whether the word has been answered correctly in a row (0 for no, 1 for yes).
- The third digit indicates whether the word is marked as requiring learning (0 for no, 1 for yes).

For example:
- **0/0/1**: The word was not answered correctly in the last attempt, has not been answered correctly in a row, and is marked as requiring learning.
- **1/0/0**: The word was answered correctly in the last attempt, has not been answered correctly in a row, and is not marked as requiring learning.

### CSV Column Names

These attributes are stored in CSV files with the following column names:
- `correct_answers`: number of correct answers (integer)
- `good_answers_in_a_row`: whether there were several consecutive correct answers (boolean)
- `good_answer`: whether the last answer was correct (boolean)
- `word_to_learn`: whether the word requires learning (boolean)

## Import File Formats

The application supports two types of CSV files:

### 1. `_words.csv` Files
These files contain words categorized by parts of speech:
- `verb`: verb
- `person`: person
- `thing`: noun
- `adjective`: adjective
- `adverb`: adverb

### 2. `_definitions.csv` Files
These files contain definitions and their corresponding words:
- `definition`: definition
- `word`: corresponding word

### File Size Limitation
Each learning set cannot contain more than {MAX_ROWS} items. Files with more rows than this limit cannot be imported, and you cannot create sets larger than this value.

### Statistics Columns (Optional)
Both file types can include statistics columns, which were previously mentioned and are used to track learning progress:
- `correct_answers` (integer)
- `good_answers_in_a_row` (boolean)
- `good_answer` (boolean)
- `word_to_learn` (boolean)

### Sample CSV File
```csv
,definition,word
0,"1 number",one
1,"2 number",two
```

### Tips
- Ensure your CSV files have the correct format and appropriate columns.
- Data import/export is available from the app's main menu.
- Words marked as "learned" will appear less frequently.
- The app automatically prioritizes words you find challenging.

## Source Code

If you are interested in the source code of this application, please visit our repository on [GitHub](https://github.com/BartoszKog/my-first-learning-app)

---

*Application created with the Flet framework (Flutter + Python)*
\\
\\
\\...
    """
    
    def __init__(self):
        super().__init__()
        self.drawer = PageProperties.get_drawer()
        
        # menu button
        self.menu_button = ft.IconButton(
            icon=ft.Icons.MENU,
            on_click=self.on_menu_click,
            icon_color=ft.Colors.WHITE
        )
        
        # Create markdown component
        markdown = ft.Markdown(
            self.MD_TEXT,
            on_tap_link=lambda e: e.page.launch_url(e.data),
            extension_set=ft.MarkdownExtensionSet.GITHUB_FLAVORED,
        )
        
        self.markdown_container = ft.ListView(
            controls=[markdown],
            expand=True,
            spacing=10,
            padding=10,
            auto_scroll=False
        )
    
    def on_menu_click(self, e):
        self.page.open(self.drawer)
        
    def did_mount(self):
        appbar = self.page.appbar
        appbar.leading = self.menu_button
        appbar.title.value = "Information"
        
        self.page.bottom_appbar.visible = False
        self.page.floating_action_button.visible = False
        
        self.page.add(self.markdown_container)
        
        self.page.update()
 
    def will_unmount(self):
        appbar = self.page.appbar
        appbar.leading = None
        self.page.update()