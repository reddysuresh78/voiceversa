import whisper
from transformers import AutoModelForSeq2SeqLM, AutoTokenizer
import sounddevice as sd
import logging

logger = logging.getLogger(__name__)

logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

"""
Provides model objects, translations etc for the application.
"""
class Globals:
    
    translation_models = {}
    whisper_model = None
    input_device = 0
    lang_to_code_map = {}
    speaker_names = {}
    customer_translations = {}
    banker_translations = {}
    you_translations = {}
    second_translations = {}
        
    @classmethod
    def initialize(cls) -> None:
        
        logger.info("Initializing translation models...") 
        models_names = [ "en-es",  "es-en", "en-zh", "zh-en", "en-tl", "tl-en" ]
        for model_name in models_names:
            model = AutoModelForSeq2SeqLM.from_pretrained(f"Helsinki-NLP/opus-mt-{model_name}")
            tokenizer = AutoTokenizer.from_pretrained(f"Helsinki-NLP/opus-mt-{model_name}") #, clean_up_tokenization_spaces=True)
            cls.translation_models[model_name] = (model, tokenizer)

        logger.info("Initializing whisper transcription model...") 
            
        cls.whisper_model = whisper.load_model("tiny")

        logger.info("Identifying input sound device...") 

        devices = sd.query_devices()
        cls.input_device = sd.default.device[0]  # [0] is the input device, [1] is the output device

        logger.info(f"Input sound device Id: {cls.input_device}" )

        cls.lang_to_code_map = { "English": "en", "Spanish": "es", "Tagalog": "tl", "Mandarin": "zh" }
        
        cls.speaker_names = { "en": "Samantha", "es": "Mónica", "tl": "Samantha", "zh": "Tingting" }
        
        cls.customer_translations = { "en": "Customer" ,"es" : "Cliente", "zh": "顾客", "tl" : "Kliyente" }

        cls.banker_translations = { "en": "Banker", "es" : "Banquero", "zh": "银行家", "tl" : "Bankero"  }
        
        cls.you_translations = { "en": "You", "es" : "Tú", "zh": "你", "tl" : "Ikaw"  }
        
        cls.second_translations = { "en": "seconds", "es" : "segundos", "zh": "秒", "tl" : "segundos" }
          
         
Globals.initialize()