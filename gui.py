import sys
import os
import threading
import random
import datetime
import requests
import traceback
import re
import yt_dlp  # Importar o yt_dlp
# Antes de importar o vlc, ajuste o PATH
if sys.platform.startswith('win'):
    os.environ['PATH'] += ';' + r'C:\Program Files\VideoLAN\VLC'  # Ajuste este caminho se necessário

import vlc
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QPushButton,
    QLabel, QHBoxLayout, QMessageBox, QComboBox, QLineEdit, QApplication
)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QImage, QPixmap
from voice import VoiceAssistant
from vision import VisionAssistant
import utils
import cv2
from chatgpt_api import ChatGPT

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Assistente Virtual")

        try:
            self.voice_assistant = VoiceAssistant()
            self.vision_assistant = VisionAssistant()
            self.chatgpt = ChatGPT()
            self.is_listening = False
            self.conversation_thread = None
            self.media_player = None  # Para reprodução de música
            self.music_mode = False  # Adicionado para controlar o modo música

            # Inicializar contexto
            self.context = []

            self.setup_ui()

            # Personalidade do Assistente
            self.assistant_name = "Eva"
            self.assistant_age = "1 ano"
            self.assistant_hobbies = ["conversar com pessoas", "aprender coisas novas", "ajudar no que for preciso"]

            # Lista de piadas para contar
            self.jokes = [
                "Por que o programador foi ao médico? Porque ele tinha muitos bugs!",
                "O que o Java disse para o C? Você tem classe!",
                "Qual é o fim da picada? Quando o mosquito vai embora."
            ]

            # Lista de elogios
            self.compliments = [
                "Você é uma pessoa incrível!",
                "Seu sorriso é contagiante!",
                "Você tem um ótimo senso de humor!"
            ]

            # Timer para atualizar a imagem da câmera
            if self.vision_assistant.camera_available:
                self.timer = QTimer()
                self.timer.timeout.connect(self.update_camera_view)
                self.timer.start(30)  # Atualiza a cada 30 ms
        except Exception as e:
            print(f"Erro ao iniciar a aplicação: {e}")
            traceback.print_exc()

    def setup_ui(self):
        self.central_widget = QWidget()
        self.layout = QVBoxLayout()

        # Display de conversação
        self.conversation_label = QLabel("Clique em 'Iniciar Conversa' para começar.")
        self.conversation_label.setAlignment(Qt.AlignLeft)
        self.conversation_label.setWordWrap(True)
        self.layout.addWidget(self.conversation_label)

        # Exibir imagem da câmera
        if self.vision_assistant.camera_available:
            self.camera_label = QLabel()
            self.camera_label.setFixedSize(640, 480)
            self.layout.addWidget(self.camera_label)
        else:
            self.camera_label = None

        # Botões
        buttons_layout = QHBoxLayout()
        self.start_button = QPushButton("Iniciar Conversa")
        self.start_button.clicked.connect(self.start_conversation)
        buttons_layout.addWidget(self.start_button)

        self.settings_button = QPushButton("Configurações")
        self.settings_button.clicked.connect(self.open_settings)
        buttons_layout.addWidget(self.settings_button)

        self.layout.addLayout(buttons_layout)

        self.central_widget.setLayout(self.layout)
        self.setCentralWidget(self.central_widget)

    def update_camera_view(self):
        try:
            frame = self.vision_assistant.capture_image()
            if frame is not None:
                # Converter imagem OpenCV (BGR) para Qt (RGB)
                rgb_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                h, w, ch = rgb_image.shape
                bytes_per_line = ch * w
                qt_image = QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format_RGB888)
                pixmap = QPixmap.fromImage(qt_image)
                self.camera_label.setPixmap(
                    pixmap.scaled(self.camera_label.width(), self.camera_label.height(), Qt.KeepAspectRatio))
        except Exception as e:
            print(f"Erro ao atualizar a visualização da câmera: {e}")
            traceback.print_exc()

    def start_conversation(self):
        if not self.is_listening:
            self.is_listening = True
            self.start_button.setText("Parar Conversa")
            self.voice_assistant.start_listening()
            self.conversation_thread = threading.Thread(target=self.conversation_flow)
            self.conversation_thread.start()
        else:
            self.is_listening = False
            self.start_button.setText("Iniciar Conversa")
            self.voice_assistant.stop_listening()
            self.update_conversation_label("Conversa encerrada.")

            # Parar música ao encerrar conversa
            if hasattr(self, 'media_player') and self.media_player is not None:
                self.media_player.stop()
                self.media_player = None
                self.music_mode = False  # Desativar o modo música

    def conversation_flow(self):
        GREETING_KEYWORDS = ["oi", "olá", "bom dia", "boa tarde", "boa noite", "e aí", "fala", "salve"]
        GREETING_RESPONSES = ["Olá!", "Oi!", "Como vai?", "É um prazer falar com você!", "Olá, como posso ajudar?", "Salve!"]
        OBJECT_QUERY_KEYWORDS = ["o que é isso", "que objeto é esse", "o que estou segurando", "o que é isto", "identifique isto"]

        ASSISTANT_NAME_QUERY = ["qual é o seu nome", "como você se chama"]
        ASSISTANT_AGE_QUERY = ["quantos anos você tem", "qual é a sua idade"]
        ASSISTANT_HOBBIES_QUERY = ["quais são seus hobbies", "o que você gosta de fazer", "do que você gosta"]
        CREATOR_QUERY = ["quem são seus criadores", "quem te criou", "quem fez você"]

        USER_EMOTION_QUERY = ["como estou me sentindo", "qual é minha emoção", "como estou", "você sabe minha emoção"]
        USER_AGE_QUERY = ["quantos anos eu tenho", "você sabe minha idade", "qual é minha idade"]
        USER_GENDER_QUERY = ["meu gênero", "qual é meu gênero", "você sabe meu sexo", "qual é meu sexo"]
        USER_RACE_QUERY = ["minha raça", "qual é minha raça", "você sabe minha etnia", "qual é minha etnia"]

        TIME_QUERY_KEYWORDS = ["que horas é agora", "que horas são", "me diga as horas", "qual é o horário", "você sabe que horas são"]
        DATE_QUERY_KEYWORDS = ["que dia é hoje", "qual a data de hoje", "qual é o dia", "qual o dia de hoje"]
        WEATHER_QUERY_KEYWORDS = ["chover hoje", "vai chover hoje", "previsão do tempo", "qual a previsão para hoje", "vai chover", "previsão de chuva"]

        PLAY_MUSIC_COMMANDS = ["tocar música", "reproduzir música", "colocar música"]
        STOP_MUSIC_COMMANDS = ["parar música", "pausar música", "stop música"]

        JOKE_COMMANDS = ["conte uma piada", "me faça rir", "diga uma piada"]
        COMPLIMENT_COMMANDS = ["me elogie", "diga algo bom sobre mim", "como estou hoje?"]

        # Contexto vazio (não salva mais histórico)
        self.context = []

        while self.is_listening:
            self.update_conversation_label("Você pode falar agora...")
            user_input = self.voice_assistant.listen()

            if not self.is_listening:
                break  # Sai do loop se is_listening for False

            if not user_input:
                self.update_conversation_label("Não entendi. Por favor, tente novamente.")
                continue

            self.update_conversation_label(f"Você: {user_input}")

            user_input_lower = user_input.lower()

            # Se estiver no modo música
            if self.music_mode:
                if any(keyword in user_input_lower for keyword in STOP_MUSIC_COMMANDS):
                    response = self.stop_music()
                else:
                    return #response = "Estou tocando música. Por favor, diga 'parar música' para interromper a música."
                self.update_conversation_label(f"Assistente: {response}")
                # Falar a resposta
                self.voice_assistant.stop_listening()
                self.voice_assistant.speak(response)
                if not self.is_listening:
                    break  # Sai do loop se is_listening for False
                self.voice_assistant.start_listening()
                continue  # Pula para a próxima iteração do loop

            try:
                # Verificar saudação
                if any(keyword in user_input_lower for keyword in GREETING_KEYWORDS):
                    response = random.choice(GREETING_RESPONSES)

                # Comandos especiais para clonagem de voz
                elif "clonar minha voz" in user_input_lower:
                    response = self.voice_assistant.clone_user_voice()
                elif "desativar clonagem de voz" in user_input_lower:
                    self.voice_assistant.using_cloned_voice = False
                    response = "Voltando para a voz padrão."

                # Reconhecimento de objetos
                elif any(keyword in user_input_lower for keyword in OBJECT_QUERY_KEYWORDS):
                    if self.vision_assistant.camera_available:
                        object_name = self.vision_assistant.recognize_object()
                        if object_name:
                            response = f"Isto parece ser um(a) {object_name}."
                        else:
                            response = "Desculpe, não consegui identificar o objeto."
                    else:
                        response = "Câmera não disponível para reconhecer objetos."

                # Perguntas sobre a personalidade do assistente
                elif any(keyword in user_input_lower for keyword in ASSISTANT_NAME_QUERY):
                    response = f"Meu nome é {self.assistant_name}."
                elif any(keyword in user_input_lower for keyword in ASSISTANT_AGE_QUERY):
                    response = f"Eu tenho {self.assistant_age} de existência."
                elif any(keyword in user_input_lower for keyword in ASSISTANT_HOBBIES_QUERY):
                    hobbies_str = ", ".join(self.assistant_hobbies)
                    response = f"Eu gosto de {hobbies_str}."
                elif any(keyword in user_input_lower for keyword in CREATOR_QUERY):
                    response = "Fui criada pelos alunos da Escola Estadual Sorama Geralda Richard Xavier do 2º ano."

                # Contar piadas
                elif any(keyword in user_input_lower for keyword in JOKE_COMMANDS):
                    response = random.choice(self.jokes)

                # Elogiar o usuário
                elif any(keyword in user_input_lower for keyword in COMPLIMENT_COMMANDS):
                    response = random.choice(self.compliments)

                # Perguntas sobre atributos faciais do usuário
                elif any(keyword in user_input_lower for keyword in USER_EMOTION_QUERY + USER_AGE_QUERY + USER_GENDER_QUERY + USER_RACE_QUERY):
                    if self.vision_assistant.camera_available:
                        attributes = self.vision_assistant.analyze_face_attributes()
                        if attributes:
                            if any(keyword in user_input_lower for keyword in USER_EMOTION_QUERY):
                                emotion = attributes.get('dominant_emotion', '')
                                if emotion:
                                    response = f"Você parece estar se sentindo {emotion}."
                                else:
                                    response = "Desculpe, não consegui determinar como você está se sentindo."

                            elif any(keyword in user_input_lower for keyword in USER_AGE_QUERY):
                                age = attributes.get('age', '')
                                if age:
                                    response = f"Você aparenta ter cerca de {int(age)} anos."
                                else:
                                    response = "Desculpe, não consegui determinar sua idade."

                            elif any(keyword in user_input_lower for keyword in USER_GENDER_QUERY):
                                gender = attributes.get('dominant_gender', '')
                                if gender:
                                    response = f"Você parece ser do gênero {gender}."
                                else:
                                    response = "Desculpe, não consegui determinar seu gênero."

                            elif any(keyword in user_input_lower for keyword in USER_RACE_QUERY):
                                race = attributes.get('dominant_race', '')
                                if race:
                                    response = f"Você parece ser de etnia {race}."
                                else:
                                    response = "Desculpe, não consegui determinar sua etnia."
                        else:
                            response = "Desculpe, não consegui analisar seus atributos faciais. Certifique-se de que seu rosto está visível para a câmera."
                    else:
                        response = "Câmera não disponível para analisar atributos faciais."

                # Consultas sobre data e hora
                elif any(keyword in user_input_lower for keyword in TIME_QUERY_KEYWORDS):
                    now = datetime.datetime.now()
                    current_time = now.strftime("%H:%M")
                    response = f"Agora são {current_time}."
                elif any(keyword in user_input_lower for keyword in DATE_QUERY_KEYWORDS):
                    now = datetime.datetime.now()
                    current_date = now.strftime("%d de %B de %Y")
                    response = f"Hoje é {current_date}."

                # Consulta sobre previsão do tempo
                elif any(keyword in user_input_lower for keyword in WEATHER_QUERY_KEYWORDS):
                    response = self.get_weather_forecast()

                # Comando para tocar música

                    # Comando para tocar música
                elif any(keyword in user_input_lower for keyword in PLAY_MUSIC_COMMANDS):
                    # Extrair nome da música do input do usuário
                    for keyword in PLAY_MUSIC_COMMANDS:
                        if keyword in user_input_lower:
                            song_name = user_input_lower.partition(keyword)[2].strip()
                            break
                    else:
                        song_name = ''
                    if song_name:
                        response = self.play_music(song_name)
                    else:
                        response = "Por favor, diga o nome da música que deseja ouvir."

                # Comando para parar música
                elif any(keyword in user_input_lower for keyword in STOP_MUSIC_COMMANDS):
                    response = self.stop_music()

                else:
                    # Obter resposta da IA usando ChatGPT
                    assistant_response = self.chatgpt.get_response(user_input, self.context)
                    response = assistant_response
                    # Adicionar a conversa ao contexto
                    self.context.append({'role': 'user', 'content': user_input})
                    self.context.append({'role': 'assistant', 'content': response})

                self.update_conversation_label(f"Assistente: {response}")

                # Desativar a escuta enquanto a IA fala
                self.voice_assistant.stop_listening()
                self.voice_assistant.speak(response)
                if not self.is_listening:
                    break  # Sai do loop se is_listening for False
                self.voice_assistant.start_listening()

            except Exception as e:
                print(f"Erro no fluxo de conversa: {e}")
                traceback.print_exc()
                self.update_conversation_label("Desculpe, ocorreu um erro ao processar sua solicitação.")
                self.is_listening = False
                self.voice_assistant.stop_listening()
                break

    def get_weather_forecast(self):
        try:
            api_key = utils.get_setting("weatherapi_api_key", "")
            if not api_key:
                return "API Key da WeatherAPI.com não configurada. Por favor, configure sua API Key nas configurações."
            city = utils.get_setting("city_name", "São Paulo")  # Cidade padrão
            url = f"http://api.weatherapi.com/v1/forecast.json?key={api_key}&q={city}&lang=pt&days=1"
            response = requests.get(url)
            data = response.json()

            if 'error' in data:
                return "Desculpe, não consegui obter a previsão do tempo no momento."

            forecast = data['forecast']['forecastday'][0]
            day = forecast['day']
            condition = day['condition']['text']
            chance_of_rain = day.get('daily_chance_of_rain', 0)

            response = f"A previsão para hoje em {city} é de {condition.lower()}."
            if int(chance_of_rain) > 0:
                response += f" Há {chance_of_rain}% de chance de chuva."
            else:
                response += " Não há previsão de chuva."
            return response
        except Exception as e:
            print(f"Erro ao obter a previsão do tempo: {e}")
            traceback.print_exc()
            return "Desculpe, não consegui obter a previsão do tempo."


    def play_music(self, song_name):
        try:
            # Pesquisar no YouTube
            search_query = song_name.replace(' ', '+')
            url = f"https://www.youtube.com/results?search_query={search_query}"
            html = requests.get(url).text
            video_ids = re.findall(r"watch\?v=(\S{11})", html)
            if not video_ids:
                return "Desculpe, não consegui encontrar a música solicitada."

            video_url = f"https://www.youtube.com/watch?v={video_ids[0]}"

            # Usar o yt_dlp para obter o URL de streaming
            ydl_opts = {
                'format': 'bestaudio/best',
                'quiet': True,
                'no_warnings': True,
            }
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info_dict = ydl.extract_info(video_url, download=False)
                audio_url = info_dict['url']
                title = info_dict.get('title', 'música')

            # Parar qualquer música que esteja tocando
            if hasattr(self, 'media_player') and self.media_player is not None:
                self.media_player.stop()

            self.instance = vlc.Instance()
            self.media_player = self.instance.media_player_new()
            media = self.instance.media_new(audio_url)
            media.get_mrl()
            self.media_player.set_media(media)
            self.media_player.play()

            self.music_mode = True  # Ativar o modo música
            return f"Iniciando a reprodução de {title}."
        except Exception as e:
            print(f"Erro ao reproduzir música: {e}")
            traceback.print_exc()
            return "Desculpe, ocorreu um erro ao tentar reproduzir a música."

    def stop_music(self):
        try:
            if hasattr(self, 'media_player') and self.media_player is not None:
                self.media_player.stop()
                self.media_player = None
                self.music_mode = False  # Desativar o modo música
                return "Música interrompida."
            else:
                return "Nenhuma música está sendo reproduzida no momento."
        except Exception as e:
            print(f"Erro ao parar música: {e}")
            traceback.print_exc()
            return "Desculpe, ocorreu um erro ao tentar parar a música."

    def update_conversation_label(self, text):
        self.conversation_label.setText(text)

    def open_settings(self):
        try:
            self.settings_window = SettingsWindow(self)
            self.settings_window.show()
        except Exception as e:
            print(f"Erro ao abrir as configurações: {e}")
            traceback.print_exc()
            QMessageBox.critical(self, "Erro", "Ocorreu um erro ao abrir as configurações.")

class SettingsWindow(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Configurações")
        self.setFixedSize(400, 400)
        self.setup_ui()

    def setup_ui(self):
        self.central_widget = QWidget()
        self.layout = QVBoxLayout()

        # Campo para API Key do OpenAI
        self.api_key_label = QLabel("API Key do OpenAI:")
        self.api_key_input = QLineEdit()
        self.api_key_input.setText(utils.get_setting("openai_api_key", ""))
        self.api_key_input.setEchoMode(QLineEdit.Password)
        self.layout.addWidget(self.api_key_label)
        self.layout.addWidget(self.api_key_input)

        # Campo para API Key do ElevenLabs
        self.elevenlabs_api_key_label = QLabel("API Key do ElevenLabs:")
        self.elevenlabs_api_key_input = QLineEdit()
        self.elevenlabs_api_key_input.setText(utils.get_setting("elevenlabs_api_key", ""))
        self.elevenlabs_api_key_input.setEchoMode(QLineEdit.Password)
        self.layout.addWidget(self.elevenlabs_api_key_label)
        self.layout.addWidget(self.elevenlabs_api_key_input)

        # Campo para API Key da WeatherAPI.com
        self.weatherapi_key_label = QLabel("API Key da WeatherAPI.com:")
        self.weatherapi_key_input = QLineEdit()
        self.weatherapi_key_input.setText(utils.get_setting("weatherapi_api_key", ""))
        self.weatherapi_key_input.setEchoMode(QLineEdit.Password)
        self.layout.addWidget(self.weatherapi_key_label)
        self.layout.addWidget(self.weatherapi_key_input)

        # Campo para o nome da cidade
        self.city_label = QLabel("Nome da Cidade:")
        self.city_input = QLineEdit()
        self.city_input.setText(utils.get_setting("city_name", ""))
        self.layout.addWidget(self.city_label)
        self.layout.addWidget(self.city_input)

        # Seleção de Microfone
        self.mic_label = QLabel("Dispositivo de Entrada de Áudio:")
        self.mic_selector = QComboBox()
        try:
            mic_list = utils.get_microphone_list()
            if not mic_list:
                mic_list = [{"index": None, "name": "Nenhum dispositivo encontrado"}]
            for mic in mic_list:
                self.mic_selector.addItem(mic['name'], mic['index'])
            # Definir o índice atual com base no índice do microfone salvo
            saved_mic_index = utils.get_setting("microphone_index", None)
            if saved_mic_index is not None:
                for i in range(self.mic_selector.count()):
                    if self.mic_selector.itemData(i) == saved_mic_index:
                        self.mic_selector.setCurrentIndex(i)
                        break
        except Exception as e:
            print(f"Erro ao obter a lista de microfones: {e}")
            traceback.print_exc()
            self.mic_selector.addItem("Erro ao carregar dispositivos", None)
        self.layout.addWidget(self.mic_label)
        self.layout.addWidget(self.mic_selector)

        # Seleção de Webcam
        self.cam_label = QLabel("Webcam:")
        self.cam_selector = QComboBox()
        try:
            cam_list = utils.get_camera_list()
            if not cam_list:
                cam_list = ["Nenhuma câmera detectada"]
            self.cam_selector.addItems(cam_list)
            self.cam_selector.setCurrentIndex(utils.get_setting("camera_index", 0))
        except Exception as e:
            print(f"Erro ao obter a lista de câmeras: {e}")
            traceback.print_exc()
            self.cam_selector.addItem("Erro ao carregar dispositivos")
        self.layout.addWidget(self.cam_label)
        self.layout.addWidget(self.cam_selector)

        # Seleção do Backend da Câmera
        self.backend_label = QLabel("Backend da Câmera:")
        self.backend_selector = QComboBox()
        backend_list = utils.get_backend_list()
        self.backend_selector.addItems(backend_list)
        current_backend = utils.get_setting("camera_backend", "AUTO")
        self.backend_selector.setCurrentText(current_backend)
        self.layout.addWidget(self.backend_label)
        self.layout.addWidget(self.backend_selector)

        # Botão Salvar
        self.save_button = QPushButton("Salvar Configurações")
        self.save_button.clicked.connect(self.save_settings)
        self.layout.addWidget(self.save_button)

        self.central_widget.setLayout(self.layout)
        self.setCentralWidget(self.central_widget)

    def save_settings(self):
        try:
            utils.set_setting("openai_api_key", self.api_key_input.text())
            utils.set_setting("elevenlabs_api_key", self.elevenlabs_api_key_input.text())
            utils.set_setting("weatherapi_api_key", self.weatherapi_key_input.text())
            utils.set_setting("city_name", self.city_input.text())
            chosen_mic_index = self.mic_selector.itemData(self.mic_selector.currentIndex())
            utils.set_setting("microphone_index", chosen_mic_index)
            utils.set_setting("camera_index", self.cam_selector.currentIndex())
            utils.set_setting("camera_backend", self.backend_selector.currentText())

            QMessageBox.information(self, "Configurações Salvas", "As configurações foram salvas com sucesso.")
            self.close()
        except Exception as e:
            print(f"Erro ao salvar as configurações: {e}")
            traceback.print_exc()
            QMessageBox.critical(self, "Erro", "Ocorreu um erro ao salvar as configurações.")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())