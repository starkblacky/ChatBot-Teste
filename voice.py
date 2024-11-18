import time
import speech_recognition as sr
from elevenlabs.client import ElevenLabs
from elevenlabs import Voice, VoiceSettings
import os
import threading
import utils
import traceback
import logging
import sys

# Importações do PyQt5
from PyQt5.QtCore import QObject, QUrl, QEventLoop
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent

# Configuração de logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('voice_assistant.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

class VoiceAssistant(QObject):
    def __init__(self):
        super().__init__()
        logging.info("Iniciando VoiceAssistant...")

        # Obter chave de API do ElevenLabs
        elevenlabs_api_key = utils.get_setting("elevenlabs_api_key", "sua_api_key_aqui")

        if not elevenlabs_api_key:
            logging.error("Chave API ElevenLabs não encontrada!")
            raise ValueError("A chave de API do ElevenLabs deve ser definida nas configurações.")

        try:
            # Configurar API do ElevenLabs
            self.eleven = ElevenLabs(api_key=elevenlabs_api_key)
            logging.info("ElevenLabs API inicializada com sucesso")
        except Exception as e:
            logging.error(f"Erro ao inicializar ElevenLabs API: {e}")
            raise

        # Verificar dispositivos de áudio disponíveis
        self._check_audio_devices()

        # Inicializar reconhecedor de voz
        self.recognizer = sr.Recognizer()
        self.recognizer.energy_threshold = 3000
        self.recognizer.dynamic_energy_threshold = True
        self.microphone_index = utils.get_setting("microphone_index", None)

        # Inicializar QMediaPlayer para reprodução de áudio
        self.player = QMediaPlayer()
        self.player.setVolume(100)  # Ajustar volume conforme necessário

        # Configurações de voz
        self.DEFAULT_VOICE = "Rachel"
        self.cloned_voice = None
        self.using_cloned_voice = False

        # Controle de threads
        self.lock = threading.Lock()
        self.should_listen = threading.Event()
        self.should_listen.set()

    def _check_audio_devices(self):
        """Verifica e lista todos os dispositivos de áudio disponíveis"""
        logging.info("Verificando dispositivos de áudio...")

        # Listar dispositivos de entrada (microfones)
        try:
            mics = sr.Microphone.list_microphone_names()
            logging.info(f"Microfones disponíveis: {mics}")
        except Exception as e:
            logging.error(f"Erro ao listar microfones: {e}")

        # Verificar dispositivos de saída do sistema
        try:
            import sounddevice as sd
            devices = sd.query_devices()
            logging.info(f"Dispositivos de áudio do sistema: {devices}")
        except Exception as e:
            logging.error(f"Erro ao verificar dispositivos de áudio do sistema: {e}")

    def listen(self):
        """Captura áudio e retorna o texto transcrito."""
        logging.info("Iniciando captura de áudio...")
        try:
            with self.lock:
                if self.microphone_index is not None:
                    mic = sr.Microphone(device_index=int(self.microphone_index))
                else:
                    mic = sr.Microphone()

                with mic as source:
                    logging.info("Ouvindo...")
                    self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
                    while self.should_listen.is_set():
                        try:
                            audio = self.recognizer.listen(source, timeout=5, phrase_time_limit=10)
                            break
                        except sr.WaitTimeoutError:
                            logging.warning("Timeout na escuta")
                            return None
                        except sr.UnknownValueError:
                            logging.warning("Áudio não reconhecido")
                            return None
                        except sr.RequestError as e:
                            logging.error(f"Erro no serviço de reconhecimento: {e}")
                            return None
                    else:
                        logging.info("Escuta interrompida")
                        return None

                try:
                    text = self.recognizer.recognize_google(audio, language='pt-BR')
                    logging.info(f"Texto reconhecido: {text}")
                    return text.strip()
                except sr.UnknownValueError:
                    logging.warning("Não entendi o que você disse.")
                    return None
                except sr.RequestError as e:
                    logging.error(f"Erro ao solicitar resultados do serviço de reconhecimento; {e}")
                    return None

        except Exception as e:
            logging.error(f"Erro ao acessar o microfone: {e}")
            traceback.print_exc()
            return None

    def speak(self, text):
        """Converte texto em fala usando o ElevenLabs e reproduz o áudio."""
        if not text:
            logging.warning("Texto vazio, nada para falar")
            return

        logging.info(f"Iniciando conversão do texto: {text[:50]}...")
        try:
            # Gerar um nome de arquivo temporário único
            temp_file = f"temp_audio_{int(time.time() * 1000)}.mp3"

            # Gerar áudio
            logging.info("Gerando áudio com ElevenLabs...")
            try:
                if self.using_cloned_voice and self.cloned_voice:
                    # Usar a voz clonada
                    audio = self.eleven.generate(
                        text=text,
                        voice=self.cloned_voice,
                        model="eleven_multilingual_v2"
                    )
                else:
                    # Usar a voz padrão
                    voices = self.eleven.voices.get_all()
                    default_voice = next((v for v in voices.voices if v.name == self.DEFAULT_VOICE), voices.voices[0])

                    audio = self.eleven.generate(
                        text=text,
                        voice=Voice(
                            voice_id=default_voice.voice_id,
                            settings=VoiceSettings(
                                stability=0.71,
                                similarity_boost=0.5,
                                style=0.0,
                                use_speaker_boost=True
                            )
                        ),
                        model="eleven_multilingual_v2"
                    )
                logging.info("Áudio gerado com sucesso")
            except Exception as e:
                logging.error(f"Erro na geração do áudio: {e}")
                raise

            # Salvar áudio em arquivo temporário
            logging.info("Salvando áudio em arquivo temporário...")
            try:
                if hasattr(audio, '__iter__'):
                    audio_bytes = b''.join(chunk for chunk in audio)
                else:
                    audio_bytes = audio

                with open(temp_file, "wb") as f:
                    f.write(audio_bytes)
                    f.flush()
                    os.fsync(f.fileno())
                logging.info("Áudio salvo com sucesso")
            except Exception as e:
                logging.error(f"Erro ao salvar arquivo de áudio: {e}")
                raise

            # Reproduzir áudio usando QMediaPlayer
            logging.info("Iniciando reprodução do áudio com QMediaPlayer...")
            try:
                # Resetar o media player
                self.player.stop()
                self.player.setMedia(QMediaContent())

                url = QUrl.fromLocalFile(os.path.abspath(temp_file))
                content = QMediaContent(url)
                self.player.setMedia(content)
                self.player.play()
                logging.info("Reprodução iniciada")

                # Esperar a reprodução terminar
                self._wait_for_audio_to_finish()

                logging.info("Reprodução concluída")
            except Exception as e:
                logging.error(f"Erro na reprodução do áudio: {e}")
                raise

            # Limpeza
            if os.path.exists(temp_file):
                os.remove(temp_file)
                logging.info("Arquivo temporário removido")

        except Exception as e:
            logging.error(f"Erro no processo de fala: {e}")
            traceback.print_exc()

    def _wait_for_audio_to_finish(self):
        """Espera a reprodução do áudio terminar."""
        loop = QEventLoop()
        self.player.mediaStatusChanged.connect(
            lambda status: loop.quit() if status == QMediaPlayer.EndOfMedia else None
        )
        loop.exec_()
        # Resetar o media player após a reprodução
        self.player.stop()
        self.player.setMedia(QMediaContent())

    def record_voice_samples(self):
        """Grava amostras da voz do usuário para clonagem."""
        samples = []
        r = sr.Recognizer()

        logging.info("Vou gravar 3 amostras da sua voz. Fale algumas frases para cada amostra.")

        for i in range(3):
            with sr.Microphone(device_index=self.microphone_index) as source:
                logging.info(f"Gravando amostra {i + 1}/3... Fale por alguns segundos.")
                # Ajustar para o ruído de fundo
                r.adjust_for_ambient_noise(source, duration=0.5)
                audio = r.listen(source, timeout=5, phrase_time_limit=10)

                # Salvar temporariamente o arquivo de áudio
                sample_filename = f"voice_sample_{i}.mp3"
                with open(sample_filename, "wb") as f:
                    f.write(audio.get_wav_data())
                samples.append(sample_filename)

        return samples

    def clone_user_voice(self):
        """Clona a voz do usuário usando as amostras gravadas."""
        try:
            samples = self.record_voice_samples()
            # Criar a voz clonada passando os nomes dos arquivos diretamente
            self.cloned_voice = self.eleven.clone(
                name="Cloned_User_Voice",
                files=samples,  # Passa os nomes dos arquivos diretamente
                description="Voz clonada do usuário"
            )
            self.using_cloned_voice = True

            # Remover as amostras de áudio
            for sample in samples:
                if os.path.exists(sample):
                    os.remove(sample)

            logging.info("Voz clonada com sucesso! Agora vou usar sua voz para responder.")
            return "Voz clonada com sucesso! Agora vou usar sua voz para responder."
        except Exception as e:
            logging.error(f"Erro ao clonar voz: {str(e)}")
            traceback.print_exc()
            return f"Erro ao clonar voz: {str(e)}"

    def stop_listening(self):
        logging.info("Parando escuta...")
        self.should_listen.clear()

    def start_listening(self):
        logging.info("Iniciando escuta...")
        self.should_listen.set()