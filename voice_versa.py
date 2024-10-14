import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton, QVBoxLayout, QHBoxLayout, QWidget, QComboBox, QLabel
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import QSize, Qt, QEvent
from chat_interface import ChatInterface
from speech_handler import SpeechHandler

import logging
import threading
import queue
from utilities import Globals

logger = logging.getLogger(__name__)

logging.basicConfig(level=logging.DEBUG, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Voice Versa")
        self.setGeometry(100, 100, 400, 300)

        banker_lang = "English"
        customer_lang = "Spanish"

        self.banker_language_var = banker_lang
        self.customer_language_var = customer_lang

        self.show_history_banker_variable = "Show History"
        self.show_history_customer_variable = "Show History"

        self.banker_lang_code = Globals.lang_to_code_map[self.banker_language_var]
        self.customer_lang_code = Globals.lang_to_code_map[self.customer_language_var]

        self.banker_speech_handler = None
        self.customer_speech_handler = None

        self.background_thread = None

        self.banker_task_queue = queue.Queue()
        self.customer_task_queue = queue.Queue()

        self.init_ui()
        self.create_chat_windows()

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        # New Session Button
        new_session_btn = QPushButton("Start New Session")
        new_session_btn.clicked.connect(self.start_new_session)
        main_layout.addWidget(new_session_btn)

        # Language Selection
        lang_layout = QHBoxLayout()
        self.banker_lang_combo = QComboBox()
        self.banker_lang_combo.addItems(["English", "Mandarin", "Spanish", "Tagalog"])
        self.banker_lang_combo.currentTextChanged.connect(lambda: self.adjust_languages(True))

        self.switch_btn = QPushButton()
        self.switch_btn.setIcon(QIcon("switch.png"))
        self.switch_btn.setIconSize(QSize(20, 20))
        self.switch_btn.clicked.connect(self.switch_languages)

        self.customer_lang_combo = QComboBox()
        self.customer_lang_combo.addItems(["English", "Mandarin", "Spanish", "Tagalog"])
        self.customer_lang_combo.currentTextChanged.connect(lambda: self.adjust_languages(False))

        lang_layout.addWidget(self.banker_lang_combo)
        lang_layout.addWidget(self.switch_btn)
        lang_layout.addWidget(self.customer_lang_combo)
        main_layout.addLayout(lang_layout)

        # Speaker Buttons
        speaker_layout = QHBoxLayout()
        self.speak_now_banker_btn = QPushButton()
        self.speak_now_banker_btn.setIcon(QIcon("record.png"))
        self.speak_now_banker_btn.clicked.connect(lambda: self.start_recording(True))

        self.cancel_speak_banker_btn = QPushButton()
        self.cancel_speak_banker_btn.setIcon(QIcon("cancel_disabled.png"))
        self.cancel_speak_banker_btn.setEnabled(False)
        self.cancel_speak_banker_btn.clicked.connect(lambda: self.cancel_recording(True))

        self.speak_now_customer_btn = QPushButton()
        self.speak_now_customer_btn.setIcon(QIcon("record.png"))
        self.speak_now_customer_btn.clicked.connect(lambda: self.start_recording(False))

        self.cancel_speak_customer_btn = QPushButton()
        self.cancel_speak_customer_btn.setIcon(QIcon("cancel_disabled.png"))
        self.cancel_speak_customer_btn.setEnabled(False)
        self.cancel_speak_customer_btn.clicked.connect(lambda: self.cancel_recording(False))

        speaker_layout.addWidget(self.speak_now_banker_btn)
        speaker_layout.addWidget(self.cancel_speak_banker_btn)
        speaker_layout.addWidget(self.speak_now_customer_btn)
        speaker_layout.addWidget(self.cancel_speak_customer_btn)
        main_layout.addLayout(speaker_layout)

        # History Buttons
        history_layout = QHBoxLayout()
        self.show_history_banker_btn = QPushButton("Show History")
        self.show_history_banker_btn.clicked.connect(lambda: self.show_history_window(True))
        self.show_history_customer_btn = QPushButton("Show History")
        self.show_history_customer_btn.clicked.connect(lambda: self.show_history_window(False))
        history_layout.addWidget(self.show_history_banker_btn)
        history_layout.addWidget(self.show_history_customer_btn)
        main_layout.addLayout(history_layout)

        self.update_language_handlers()

    def adjust_languages(self, is_banker=False):
        banker_lang = self.banker_language_var
        customer_lang = self.customer_language_var

        if banker_lang != customer_lang and (banker_lang == "English" or customer_lang == "English"):
            self.update_language_handlers()
            self.start_new_session()
            return

        if is_banker:
            if banker_lang != "English":
                self.customer_language_var = "English"
            else:
                self.customer_language_var = "Spanish"
        else:
            if customer_lang != "English":
                self.banker_language_var = "English"
            else:
                self.banker_language_var = "Spanish"

        self.update_language_handlers()
        self.start_new_session()

    def update_language_handlers(self):
        self.banker_speech_handler = SpeechHandler(self.banker_language_var, self.customer_language_var, self.banker_task_queue)
        self.customer_speech_handler = SpeechHandler(self.customer_language_var, self.banker_language_var, self.customer_task_queue)
        self.banker_lang_code = Globals.lang_to_code_map[self.banker_language_var]
        self.customer_lang_code = Globals.lang_to_code_map[self.customer_language_var]

    def start_recording(self, is_banker=False):
        logger.info(f"start_recording called. is_banker: {is_banker}")
        if is_banker:
            if self.speak_now_banker_btn.icon().name() == "stop.png":
                logger.info("Stopping banker recording")
                self.speak_now_banker_btn.setIcon(QIcon("record.png"))
                self.cancel_speak_banker_btn.setIcon(QIcon("cancel_disabled.png"))
                self.cancel_speak_banker_btn.setEnabled(False)
                if self.banker_speech_handler is not None:
                    self.banker_speech_handler.stop_recording()
                    if self.background_thread is not None:
                        self.background_thread.join()  # Wait for the thread to finish
                        self.background_thread = None
            else:
                logger.info("Starting banker recording")
                self.speak_now_banker_btn.setIcon(QIcon("stop.png"))
                self.cancel_speak_banker_btn.setIcon(QIcon("cancel.png"))
                self.cancel_speak_banker_btn.setEnabled(True)

                if self.background_thread is None or not self.background_thread.is_alive():
                    logger.info("Creating new background thread for banker recording")
                    self.background_thread = threading.Thread(target=self.banker_speech_handler.start_turn)
                    self.background_thread.start()
        else:
            if self.speak_now_customer_btn.icon().name() == "stop.png":
                logger.info("Stopping customer recording")
                self.speak_now_customer_btn.setIcon(QIcon("record.png"))
                self.cancel_speak_customer_btn.setIcon(QIcon("cancel_disabled.png"))
                self.cancel_speak_customer_btn.setEnabled(False)
                if self.customer_speech_handler is not None:
                    self.customer_speech_handler.stop_recording()
                    if self.background_thread is not None:
                        self.background_thread.join()  # Wait for the thread to finish
                        self.background_thread = None
            else:
                logger.info("Starting customer recording")
                self.speak_now_customer_btn.setIcon(QIcon("stop.png"))
                self.cancel_speak_customer_btn.setIcon(QIcon("cancel.png"))
                self.cancel_speak_customer_btn.setEnabled(True)

                if self.background_thread is None or not self.background_thread.is_alive():
                    logger.info("Creating new background thread for customer recording")
                    self.background_thread = threading.Thread(target=self.customer_speech_handler.start_turn)
                    self.background_thread.start()

        logger.info("start_recording method completed")

    def cancel_recording(self, is_banker=False):
        if is_banker:
            self.speak_now_banker_btn.setIcon(QIcon("record.png"))
            self.cancel_speak_banker_btn.setIcon(QIcon("cancel_disabled.png"))
            self.cancel_speak_banker_btn.setEnabled(False)
            if self.banker_speech_handler is not None:
                self.banker_speech_handler.cancel_recording()
        else:
            self.speak_now_customer_btn.setIcon(QIcon("record.png"))
            self.cancel_speak_customer_btn.setIcon(QIcon("cancel_disabled.png"))
            self.cancel_speak_customer_btn.setEnabled(False)
            if self.customer_speech_handler is not None:
                self.customer_speech_handler.cancel_recording()

    def start_new_session(self):
        if hasattr(self, 'banker_chat'):
            self.banker_chat.clear_messages()
        if hasattr(self, 'customer_chat'):
            self.customer_chat.clear_messages()

    def show_history_window(self, is_banker=False):
        if is_banker:
            if self.show_history_banker_variable == "Hide History":
                self.hide_history_window(is_banker)
                return

            self.banker_history_window.show()
            self.banker_history_window.activateWindow()
            self.show_history_banker_variable = "Hide History"
        else:
            if self.show_history_customer_variable == "Hide History":
                self.hide_history_window(is_banker)
                return

            self.customer_history_window.show()
            self.customer_history_window.activateWindow()
            self.show_history_customer_variable = "Hide History"

    def hide_history_window(self, is_banker=False):
        if is_banker:
            if hasattr(self, 'banker_history_window'):
                self.banker_history_window.hide()
                self.show_history_banker_variable = "Show History"
        else:
            if hasattr(self, 'customer_history_window'):
                self.customer_history_window.hide()
                self.show_history_customer_variable = "Show History"

    def switch_languages(self):
        self.start_new_session()
        temp = self.banker_language_var
        self.banker_language_var = self.customer_language_var
        self.customer_language_var = temp

    def create_chat_history_window(self, title: str, is_banker=False):
        history_window = QWidget()
        history_window.setWindowTitle("Chat History - " + title)

        window_width = 600
        window_height = 500

        window_y_cordinate = 10
        window_x_cordinate = 10 if is_banker else window_width + 100

        history_window.setGeometry(window_x_cordinate, window_y_cordinate, window_width, window_height)
        history_window.setMinimumSize(window_width, window_height)

        history_window.setWindowFlags(Qt.Window)

        if is_banker:
            self.banker_chat = ChatInterface(master=history_window, height=400)
            self.banker_chat.setParent(history_window)
        else:
            self.customer_chat = ChatInterface(master=history_window, height=400)
            self.customer_chat.setParent(history_window)

        close_button = QPushButton("Close")
        close_button.clicked.connect(lambda: self.hide_history_window(is_banker))

        layout = QVBoxLayout(history_window)
        layout.addWidget(self.banker_chat if is_banker else self.customer_chat)
        layout.addWidget(close_button)

        history_window.hide()

        return history_window

    def create_chat_windows(self):
        self.banker_history_window = self.create_chat_history_window("Banker", True)
        self.customer_history_window = self.create_chat_history_window("Customer", False)

    def check_banker_queue(self):
        try:
            result = self.banker_task_queue.get_nowait()
            logger.debug(f"Queue result:  {result}")
            if result.startswith("transcript"):
                logger.debug(f"Transcript: {result}")
                self.banker_chat.add_message(result[11:], Globals.you_translations[self.banker_lang_code], "mine", self.banker_lang_code)
            elif  result.startswith("translated"):
                self.customer_chat.add_message(result[11:], Globals.banker_translations[self.customer_lang_code] , "other", self.customer_lang_code)
                self.customer_chat.add_addendum("mine","")
            elif  result.startswith("total_time:"):
                seconds = result[ 11: ]
                logger.debug(f"Total Time: {result}" )
                self.banker_chat.add_addendum("mine" , seconds + " " + Globals.second_translations[self.banker_lang_code])
        except queue.Empty:
            pass
        finally:
            QApplication.instance().processEvents()
            QApplication.instance().postEvent(self, Qt.QEvent(Qt.QEvent.User))

    def check_customer_queue(self):
        try:
            result = self.customer_task_queue.get_nowait()
            logger.debug(f"Queue result:  {result}")
            if result.startswith("transcript"):
                logger.debug(f"Transcript: {result}")
                self.customer_chat.add_message(result[11:], Globals.you_translations[self.customer_lang_code], "mine", self.customer_lang_code)
            elif  result.startswith("translated"):
                self.banker_chat.add_message(result[11:], Globals.customer_translations[self.banker_lang_code] , "other", self.banker_lang_code)
                self.banker_chat.add_addendum("mine","")
            elif  result.startswith("total_time:"):
                seconds = result[ 11: ]
                logger.debug(f"Total Time: {result}" )
                self.customer_chat.add_addendum("mine" , seconds + " " + Globals.second_translations[self.customer_lang_code])
        except queue.Empty:
            pass
        finally:
            QApplication.instance().processEvents()
            QApplication.instance().postEvent(self, Qt.QEvent(Qt.QEvent.User))

    def event(self, event):
        if event.type() == QEvent.Type.User:
            self.check_banker_queue()
            self.check_customer_queue()
            return True
        return super().event(event)

def main():
    app = QApplication(sys.argv)
    main_window = MainWindow()
    main_window.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()