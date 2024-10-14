from PyQt5.QtWidgets import QWidget, QVBoxLayout, QTextEdit, QScrollArea
from PyQt5.QtGui import QTextCursor
from PyQt5.QtCore import Qt

class ChatInterface(QWidget):
    def __init__(self, master=None, height=400):
        super().__init__(master)
        self.layout = QVBoxLayout(self)
        
        self.chat_area = QTextEdit()
        self.chat_area.setReadOnly(True)
        
        scroll_area = QScrollArea()
        scroll_area.setWidget(self.chat_area)
        scroll_area.setWidgetResizable(True)
        scroll_area.setFixedHeight(height)
        
        self.layout.addWidget(scroll_area)

    def add_message(self, message, sender, message_type, lang_code):
        self.chat_area.append(f"{sender}: {message}")
        self.chat_area.moveCursor(QTextCursor.End)

    def add_addendum(self, message_type, addendum):
        self.chat_area.append(f"({addendum})")
        self.chat_area.moveCursor(QTextCursor.End)

    def clear_messages(self):
        self.chat_area.clear()
