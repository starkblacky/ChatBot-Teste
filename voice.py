# voice.py
import speech_recognition as sr
import pyttsx3
import utils
import threading

class VoiceAssistant:
    def __init__(self):
        self.recognizer = sr.Recognizer()
        self.microphone_index = utils.get_setting("microphone_index", 0)
        self.engine = pyttsx3.init()
        self.configure_voice_engine()
        self.lock = threading.Lock()

    def configure_voice_engine(self):
        voices = self.engine.getProperty('voices')
        # Escolhe a voz em português se disponível
        for voice in voices:
            try:
                # Verifica se há idiomas disponíveis e se são do tipo bytes
                if hasattr(voice, 'languages') and voice.languages:
                    language = voice.languages[0]
                    if isinstance(language, bytes):
                        language = language.decode()
                    elif isinstance(language, str):
                        language = language
                    else:
                        continue

                    if "portuguese" in language.lower():
                        self.engine.setProperty('voice', voice.id)
                        break
            except (IndexError, AttributeError, UnicodeDecodeError):
                continue

    def listen(self):
        try:
            with sr.Microphone(device_index=self.microphone_index) as source:
                audio = self.recognizer.listen(source)
            text = self.recognizer.recognize_google(audio, language='pt-BR')
            return text
        except sr.UnknownValueError:
            return None
        except sr.RequestError:
            return None

    def speak(self, text):
        self.engine.say(text)
        self.engine.runAndWait()