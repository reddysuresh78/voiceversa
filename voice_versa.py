import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton, QVBoxLayout, QWidget, QComboBox, QTextEdit
from PyQt5.QtCore import QTimer
from speech_handler import SpeechHandler
import logging

logger = logging.getLogger(__name__)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Voice Translator")
        self.setGeometry(100, 100, 400, 400)

        self.speech_handler = SpeechHandler()

        self.init_ui()

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        self.source_lang_combo = QComboBox()
        self.source_lang_combo.addItems(["English", "Spanish", "French", "German"])
        layout.addWidget(self.source_lang_combo)

        self.target_lang_combo = QComboBox()
        self.target_lang_combo.addItems(["Spanish", "French", "German", "English"])
        layout.addWidget(self.target_lang_combo)

        self.record_button = QPushButton("Record (5 seconds)")
        self.record_button.clicked.connect(self.toggle_recording)
        layout.addWidget(self.record_button)

        self.play_button = QPushButton("Play")
        self.play_button.clicked.connect(self.play_audio)
        layout.addWidget(self.play_button)

        self.translate_button = QPushButton("Translate")
        self.translate_button.clicked.connect(self.translate_audio)
        layout.addWidget(self.translate_button)

        self.transcription_text = QTextEdit()
        self.transcription_text.setPlaceholderText("Transcription will appear here")
        layout.addWidget(self.transcription_text)

        self.translation_text = QTextEdit()
        self.translation_text.setPlaceholderText("Translation will appear here")
        layout.addWidget(self.translation_text)

    def toggle_recording(self):
        if not self.speech_handler.is_recording:
            self.record_button.setText("Recording...")
            self.record_button.setEnabled(False)
            self.speech_handler.start_recording()
            QTimer.singleShot(5000, self.stop_recording)
        else:
            self.stop_recording()

    def stop_recording(self):
        self.speech_handler.stop_recording()
        self.record_button.setText("Record (5 seconds)")
        self.record_button.setEnabled(True)

    def play_audio(self):
        self.speech_handler.play_audio()

    def translate_audio(self):
        transcription = self.speech_handler.transcribe()
        self.transcription_text.setText(transcription)

        source_lang = self.source_lang_combo.currentText().lower()
        target_lang = self.target_lang_combo.currentText().lower()
        translation = self.speech_handler.translate(transcription, source_lang, target_lang)
        self.translation_text.setText(translation)

def main():
    app = QApplication(sys.argv)
    main_window = MainWindow()
    main_window.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
