import sys
import sqlite3
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel, QPushButton, QLineEdit, QGridLayout, QSizePolicy, QScrollArea
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFontMetrics
from core import *
import tracemalloc

tracemalloc.start()

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Main Window')
        self.setGeometry(100, 100, 800, 600)
        self.generate_main_page()

    def generate_main_page(self):
        self.layout = QGridLayout()

        # Define the number of rows and columns
        num_rows = 15
        num_columns = 15
        show_coordinates = False
        # Add empty placeholders to set up the grid
        for i in range(num_rows):
            for j in range(num_columns):
                # Create an empty QWidget as a placeholder
                if show_coordinates:
                    empty_widget = QLabel(f'({i},{j})', self)
                else:
                    empty_widget = QWidget(self)
                empty_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
                # Add the empty widget to the grid layout
                self.layout.addWidget(empty_widget, i, j)

        self.label = QLabel('Type Something:')
        self.layout.addWidget(self.label, 5, 7)

        self.typing_box = QLineEdit()
        self.layout.addWidget(self.typing_box, 6, 7)

        submit_button = QPushButton('Submit')
        submit_button.clicked.connect(self.on_submit)
        submit_button.setFixedWidth(200)
        self.layout.addWidget(submit_button, 7, 7)


        self.setLayout(self.layout)

    def regenerate_main_page(self):
        self.clear_layout()

        # Define the number of rows and columns
        num_rows = 15
        num_columns = 15
        show_coordinates = False
        # Add empty placeholders to set up the grid
        for i in range(num_rows):
            for j in range(num_columns):
                # Create an empty QWidget as a placeholder
                if show_coordinates:
                    empty_widget = QLabel(f'({i},{j})', self)
                else:
                    empty_widget = QWidget(self)
                empty_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
                # Add the empty widget to the grid layout
                self.layout.addWidget(empty_widget, i, j)

        self.label = QLabel('Type Something:')
        self.layout.addWidget(self.label, 5, 7)

        self.typing_box = QLineEdit()
        self.layout.addWidget(self.typing_box, 6, 7)

        submit_button = QPushButton('Submit')
        submit_button.clicked.connect(self.on_submit)
        submit_button.setFixedWidth(200)
        self.layout.addWidget(submit_button, 7, 7)

    def on_submit(self):
        submitted_text = self.typing_box.text()
        print(f"Submitted text: {submitted_text}")

        db_path = 'db/music_database.db'
        database_setup(db_path)

        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        query = "SELECT 1 FROM artist WHERE spotify_id = ? LIMIT 1"
        cursor.execute(query, (submitted_text,))
        result = cursor.fetchone()
        conn.close()

        if result is None:
            print('Artist does not exist in database, beginning database population...')
            rules, key_dictionary, first_chord_dictionary = populate_database(submitted_text, db_path)
            print('keys:', key_dictionary)
            print('first chord:', first_chord_dictionary)
            rules = format_rules(rules)
            print('rules:', rules)
        else:
            print('Artist exists in database...')
            progressions, key_dictionary, first_chord_dictionary = pull_from_database(submitted_text, db_path)
            rules = rule_mining(progressions)
            print('keys:', key_dictionary)
            print('first chord:', first_chord_dictionary)
            rules = format_rules(rules)
            print('rules:', rules)

        self.generate_stats_page(rules, key_dictionary, first_chord_dictionary)

    # def generate_loading_page(self):
    #     self.clear_layout()
    # 
    #     # Define the number of rows and columns
    #     num_rows = 15
    #     num_columns = 15
    #     show_coordinates = False
    #     # Add empty placeholders to set up the grid
    #     for i in range(num_rows):
    #         for j in range(num_columns):
    #             # Create an empty QWidget as a placeholder
    #             if show_coordinates:
    #                 empty_widget = QLabel(f'({i},{j})', self)
    #             else:
    #                 empty_widget = QWidget(self)
    #             empty_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
    #             # Add the empty widget to the grid layout
    #             self.layout.addWidget(empty_widget, i, j)

    def generate_stats_page(self, rules, key_dictionary, first_chord_dictionary):
        self.clear_layout()

        # Define the number of rows and columns
        num_rows = 15
        num_columns = 15
        show_coordinates = False
        # Add empty placeholders to set up the grid
        for i in range(num_rows):
            for j in range(num_columns):
                # Create an empty QWidget as a placeholder
                if show_coordinates:
                    empty_widget = QLabel(f'({i},{j})', self)
                else:
                    empty_widget = QWidget(self)
                empty_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
                # Add the empty widget to the grid layout
                self.layout.addWidget(empty_widget, i, j)

        keys_label = QLabel('Common Keys:')
        self.layout.addWidget(keys_label, 0, 0, 1, 10)
        keys_content = QLabel(str(key_dictionary[:5]))
        self.layout.addWidget(keys_content, 1, 0, 1, 10)

        keys_label = QLabel('Common Starting Chords:')
        self.layout.addWidget(keys_label, 2, 0, 1, 10)
        keys_content = QLabel(str(first_chord_dictionary[:5]))
        self.layout.addWidget(keys_content, 3, 0, 1, 10)

        keys_label = QLabel('Rules:')
        self.layout.addWidget(keys_label, 4, 0, 1, 10)
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)  # Disable horizontal scrolling
        font_metrics = QFontMetrics(self.font())
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        max_width = 0
        for value in rules.values():
            display_string = f'{value["antecedents"]} -> {value["consequents"]} support: {value["support"]} confidence: {value["confidence"]}'
            content_layout.addWidget(QLabel(display_string))
            text_width = font_metrics.boundingRect(display_string).width()
            max_width = max(max_width, text_width)
        # Add some padding for the scroll area width
        padding = 100
        scroll_area.setFixedWidth(max_width + padding)

        # Set the content widget to the scroll area
        scroll_area.setWidget(content_widget)

        # Add the scroll area to the grid layout at row 0, column 0
        self.layout.addWidget(scroll_area, 5, 0, 9, 10)

        back_button = QPushButton('Back')
        back_button.setFixedWidth(200)
        back_button.clicked.connect(self.regenerate_main_page)  # Reinitialize the main UI
        self.layout.addWidget(back_button, 14, 6, 1, 10)

        self.setLayout(self.layout)

    def clear_layout(self):
        while self.layout.count():
            child = self.layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    main_window = MainWindow()
    main_window.show()
    sys.exit(app.exec_())