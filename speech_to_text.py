import torch
import whisper
from text_to_sign import main_sign
class WhisperSTT:
    def __init__(self, model_size='small'):
        self.device = 'cuda' if torch.cuda.is_available() else 'cpu'
        self.model = whisper.load_model(model_size).to(self.device)
    
    def transcribe(self, audio_path, language=None):
        options = {
            'fp16': torch.cuda.is_available(), 
            'language': language  
        }

        result = self.model.transcribe(audio_path, **options)
        
        return {
            'text': result['text'],
            'language': result['language'],
            'segments': result['segments']
        }
    
    def translate(self, audio_path):
        options = {
            'task': 'translate',
            'fp16': torch.cuda.is_available()
        }
        
        result = self.model.transcribe(audio_path, **options)
        
        return {
            'text': result['text'],
            'source_language': result['language']
        }
    
def main_text(path):
    stt = WhisperSTT(model_size='small')
    result = stt.transcribe(path, language='en')
    print(result['text'])   
    return main_sign(result['text'])