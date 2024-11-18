# voice.py
import speech_recognition as sr
import pyttsx3
import utils
import threading
import traceback
import sounddevice as sd
import numpy as np

class VoiceAssistant:
    def __init__(self):
        self.recognizer = sr.Recognizer()
        self.microphone_index = utils.get_setting("microphone_index", None)
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

                    if "pt" in language.lower() or "portuguese" in language.lower():
                        self.engine.setProperty('voice', voice.id)
                        break
                else:
                    # Alguns motores de voz não têm o atributo 'languages', então verificamos o 'name'
                    if "português" in voice.name.lower() or "portuguese" in voice.name.lower():
                        self.engine.setProperty('voice', voice.id)
                        break
            except (IndexError, AttributeError, UnicodeDecodeError):
                continue

    def listen(self):
        try:
            # Usar sounddevice para capturar o áudio
            samplerate = 16000  # Taxa de amostragem padrão
            duration = 5  # Segundos para gravar (ajuste conforme necessário)
            print("Ouvindo...")
            with self.lock:
                if self.microphone_index is not None:
                    device_index = int(self.microphone_index)
                else:
                    device_index = None  # Dispositivo padrão
                recording = sd.rec(int(samplerate * duration), samplerate=samplerate, channels=1, dtype='int16', device=device_index)
                sd.wait()  # Espera a gravação terminar

                audio_data = np.squeeze(recording)
                audio_bytes = audio_data.tobytes()
                audio = sr.AudioData(audio_bytes, samplerate, 2)  # 2 bytes por amostra (int16)

            try:
                text = self.recognizer.recognize_google(audio, language='pt-BR')
                print(f"Você disse: {text}")
                return text
            except sr.UnknownValueError:
                print("Não entendi o que você disse.")
                return None
            except sr.RequestError as e:
                print(f"Erro ao solicitar resultados do serviço de reconhecimento; {e}")
                return None
        except Exception as e:
            print(f"Erro ao acessar o microfone: {e}")
            traceback.print_exc()
            return None

    def speak(self, text):
        self.engine.say(text)
        self.engine.runAndWait()