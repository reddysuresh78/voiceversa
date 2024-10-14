import numpy as np
import threading
import queue
import subprocess
from utilities import Globals
from datetime import datetime as time
import logging
import sounddevice as sd
 
  
logger = logging.getLogger(__name__)

logging.basicConfig(level=logging.DEBUG, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
"""
Class to handle speech input and output.
"""
class SpeechHandler:
     
    def __init__(self, input_langugage, target_language, task_queue):
        
        self.input_language = input_langugage
        self.target_language = target_language
        self.input_lang_code = Globals.lang_to_code_map[input_langugage]
        self.target_lang_code = Globals.lang_to_code_map[target_language]

        self.task_queue = task_queue
    
        # flags to control recording
        self.is_recording = True
        self.is_cancelled = False
        self.recorded_audio = None
              
    """
    Records the voice using sounddevice and stores it in a buffer until user 
    either stops or cancels the recording.
    """
    def record_audio(self, samplerate=16000, channels=2):
        q = queue.Queue()
        self.recorded_audio = None

        def recording_callback(indata, frames, time, status):
            logger.info(f"Recording callback called. Frames: {frames}, Status: {status}")
            if status:
                logger.warning(f"Recording status: {status}")
            if np.any(indata):
                logger.info("Audio input detected")
            else:
                logger.warning("No audio input detected in this chunk")
            q.put(indata.copy())
        
        logger.info(f"Starting recording with device: {Globals.input_sound_device}")
        try:
            with sd.InputStream(samplerate=samplerate, channels=channels, device=Globals.input_sound_device, callback=recording_callback, blocksize=samplerate * 2, dtype='int16'):
                logger.info("InputStream opened successfully")
                recorded_frames = []
                while self.is_recording:
                    try:
                        frame = q.get(timeout=1)  # Wait for 1 second
                        recorded_frames.append(frame)
                        logger.debug(f"Recorded frame added. Total frames: {len(recorded_frames)}")
                    except queue.Empty:
                        if not self.is_recording:
                            break
                        else:
                            continue

            logger.info("Recording stopped. Processing recorded frames.")
            if recorded_frames:
                recording = np.concatenate(recorded_frames, axis=0)
                self.recorded_audio = recording
                logger.info(f"Recording processed. Shape: {recording.shape}")
            else:
                logger.warning("No frames were recorded")

        except Exception as e:
            logger.error(f"Error during recording: {e}")

        return self.recorded_audio
 
    """
    Starts the recording in a separate thread.
    """
    def start_recording(self, samplerate=16000, channels=1): 
        self.is_recording = True
        recording_thread = threading.Thread(target=lambda: self.record_audio( samplerate, channels))
        recording_thread.start()
        return recording_thread
    """
    Stops the recording by setting the flag to false.
    """
    def stop_recording(self):
        logger.debug("Stopping recording...")
        self.is_recording = False
        logger.debug("Recording flag set to false")

    """
    Cancels the recording by setting the flag to false and clearing the queue.
    """
    def cancel_recording(self):
        logger.debug("Is recording set to false now")
        self.is_recording = False
        self.is_cancelled = True
  
    """
    Traanscribes the audio to text using whisper model.
    """
    def transcribe(self):
        logger.debug("Now transcribing")
        
        buffer =  self.recorded_audio.flatten().astype(np.float32) / 32768.0
        result = Globals.whisper_model.transcribe(buffer, language= self.input_language)
         
        logger.info(f'The text in audio: \n {result["text"]}')
        return result["text"]
       
    """
    Translates the text to target language using Helsinki-NLP model for given language pair.
    """
    def translate(self, input_text):
    
        model_code = self.input_lang_code  + "-" + self.target_lang_code
        (model, tokenizer) = Globals.translation_models[model_code]
        
        logger.info(f"Trying to translate:  {input_text}")
        
        inputs = tokenizer(input_text, return_tensors="pt")
        outputs = model.generate(**inputs, max_new_tokens=1024)
        translated = tokenizer.batch_decode(outputs, skip_special_tokens=True)
        
        logger.info(f"Translated text:  {translated}" )
        
        return translated[0]
    
    """
    This function speaks the given message using the system's built-in text-to-speech engine.
    This method is primarily used on Mac and this won't work on windows. 
    
    For windows: 
    
    * pyttsx3 to be installed 
    * And additional languagepacks to be downloaded for Spanish, Chinese and Tagalog. 
    """
    def speak(self, message):
        
        voice = Globals.speaker_names[self.target_lang_code]
        
        logger.debug(f"Speaking: {message} -  {self.target_language} - {voice}") 

        try:
            result = subprocess.run(["say", '-v', voice, message], capture_output=True, text=True, check=True)
            logger.info(f"Speech command executed successfully: {result.stdout}")
        except subprocess.CalledProcessError as e:
            logger.error(f"Error executing speech command: {e}")
            logger.error(f"Error output: {e.stderr}")
        except Exception as e:
            logger.error(f"Unexpected error in speak method: {e}")
        
        self.task_queue.put("play_over")
    

    """
    Starts turn means it handles one user input, transacription, translation and speaking 
    it in target language
    """
    def start_turn(self):
 
        self.is_cancelled = False

        self.task_queue.queue.clear()

        thread = self.start_recording( )  # Start recording in a thread
    
        thread.join()  # Wait for the recording thread to finish

        if self.is_cancelled:
            logger.debug("Recording cancelled. So not proceeding with next steps")
            return

        logger.debug("Recording stopped.")

        startTime = time.now()
        prevTime = time.now()
    
        if self.recorded_audio is None:
            logger.warning("No audio recorded. Skipping transcription and translation.")
            return

        transcribed_text =  self.transcribe()
        
        self.task_queue.put("transcript:" + transcribed_text)

        logger.debug(f"Transcription over, time: {time.now() - prevTime}")
    
        prevTime = time.now()
        
        translated_text = self.translate(transcribed_text)
        
        self.task_queue.put("translated:" + translated_text)

        logger.debug(f"translation over, time: {time.now() - prevTime}")
        
        elapsed_time = (time.now() - startTime).total_seconds()
        
        self.task_queue.put(f"total_time: {elapsed_time:.1f}")

        prevTime = time.now()
      
        logger.info(f"Target audio delivered, time: {time.now() - prevTime}")
        
        self.speak(translated_text)
        
    
    
    


    


