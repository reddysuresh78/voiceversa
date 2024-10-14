import numpy as np
import threading
import queue
import sounddevice as sd
import soundfile as sf
import logging
import torch
from transformers import pipeline
import os
from utilities import Globals

# Add this line at the beginning of your file, after the imports
os.environ['PYTORCH_ENABLE_MPS_FALLBACK'] = '1'


logger = logging.getLogger(__name__)

class SpeechHandler:
    def __init__(self):
        self.is_recording = False
        self.recorded_audio = None
        self.sample_rate = 44100  # Standard sample rate
        
        # Determine the device to use
        #device = "mps" if torch.backends.mps.is_available() else "cpu"
        device = "cpu"
        
        self.transcriber = pipeline("automatic-speech-recognition", 
                                    model="openai/whisper-small", 
                                    device=device)
        
        self.translator = pipeline("translation", 
                                   model="Helsinki-NLP/opus-mt-en-ROMANCE", 
                                   device=device)
        
        logger.info(f"Using device: {device}")

    def record_audio(self):
        logger.info("Starting audio recording...")
        self.recorded_audio = sd.rec(int(5 * self.sample_rate), samplerate=self.sample_rate, channels=1)
        sd.wait()
        logger.info("Audio recording completed.")

    def play_audio(self):
        if self.recorded_audio is not None:
            logger.info("Playing recorded audio...")
            sd.play(self.recorded_audio, self.sample_rate)
            sd.wait()
            logger.info("Audio playback completed.")
        else:
            logger.warning("No audio recorded to play.")

    def start_recording(self):
        self.is_recording = True
        recording_thread = threading.Thread(target=self.record_audio)
        recording_thread.start()
        return recording_thread

    def stop_recording(self):
        self.is_recording = False
        logger.info("Recording stopped.")

    def save_audio(self, filename="recorded_audio.wav"):
        if self.recorded_audio is not None:
            sf.write(filename, self.recorded_audio, self.sample_rate)
            logger.info(f"Audio saved to {filename}")
        else:
            logger.warning("No audio recorded to save.")

    def transcribe(self):
        if self.recorded_audio is not None:
            audio = self.recorded_audio.flatten()
            result = self.transcriber(audio)
            return result["text"]
        else:
            logger.warning("No audio recorded to transcribe.")
            return ""

    def translate(self, text, source_lang, target_lang):
        # Implementation here
        pass

    def get_language_code(self, language):
        language_codes = {
            'english': 'en',
            'spanish': 'es',
            'french': 'fr',
            'german': 'de'
        }
        return language_codes.get(language.lower(), 'en')
