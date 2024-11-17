# gui.py
import threading
import random
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QPushButton,
    QLabel, QHBoxLayout, QLineEdit, QMessageBox, QComboBox
)
from PyQt5.QtCore import Qt
from chatgpt_api import ChatGPT
from voice import VoiceAssistant
from vision import VisionAssistant
import database
import utils
import traceback

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Assistente Virtual")

        try:
            self.chatgpt = ChatGPT()
            self.voice_assistant = VoiceAssistant()
            self.vision_assistant = VisionAssistant()
            self.context = []
            self.is_listening = False

            self.setup_ui()

            # Personalidade do Assistente
            self.assistant_name = "Eva"
            self.assistant_age = "1 ano"
            self.assistant_hobbies = ["conversar com pessoas", "aprender coisas novas", "ajudar no que for preciso"]
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

    def start_conversation(self):
        if not self.is_listening:
            self.is_listening = True
            self.start_button.setText("Parar Conversa")
            threading.Thread(target=self.conversation_flow).start()
        else:
            self.is_listening = False
            self.start_button.setText("Iniciar Conversa")
            self.conversation_label.setText("Conversa encerrada.")

    def conversation_flow(self):
        user_name = "Desconhecido"
        user_registered = False
        known_encodings = database.get_known_encodings()
        known_users = database.get_user_names()

        GREETING_KEYWORDS = ["oi", "olá", "bom dia", "boa tarde", "boa noite", "e aí", "fala", "salve"]
        GREETING_RESPONSES = ["Olá!", "Oi!", "Como vai?", "É um prazer falar com você!", "Olá, como posso ajudar?", "Salve!"]
        OBJECT_QUERY_KEYWORDS = ["o que é isso", "que objeto é esse", "o que estou segurando", "o que é isto", "identifique isto"]
        NAME_QUERY_KEYWORDS = ["você sabe meu nome", "qual é o meu nome", "quem sou eu", "me reconhece"]

        ASSISTANT_NAME_QUERY = ["qual é o seu nome", "como você se chama"]
        ASSISTANT_AGE_QUERY = ["quantos anos você tem", "qual é a sua idade"]
        ASSISTANT_HOBBIES_QUERY = ["quais são seus hobbies", "o que você gosta de fazer", "do que você gosta"]

        USER_EMOTION_QUERY = ["como estou me sentindo", "qual é minha emoção", "como estou", "você sabe minha emoção"]
        USER_AGE_QUERY = ["quantos anos eu tenho", "você sabe minha idade", "qual é minha idade"]
        USER_GENDER_QUERY = ["qual é meu gênero", "você sabe meu sexo", "qual meu sexo"]
        USER_RACE_QUERY = ["qual é minha raça", "você sabe minha etnia", "qual é minha etnia"]

        while self.is_listening:
            self.update_conversation_label("Você pode falar agora...")
            user_input = self.voice_assistant.listen()
            if not user_input:
                self.update_conversation_label("Não entendi. Por favor, tente novamente.")
                continue

            self.update_conversation_label(f"Você: {user_input}")

            user_input_lower = user_input.lower()

            try:
                # Verificar saudação
                if any(keyword in user_input_lower for keyword in GREETING_KEYWORDS):
                    response = random.choice(GREETING_RESPONSES)

                # Verificar registro do usuário
                elif "meu nome é" in user_input_lower:
                    if self.vision_assistant.camera_available:
                        user_name = user_input_lower.split("meu nome é")[1].strip().capitalize()
                        # Registrar usuário
                        encoding = self.vision_assistant.encode_face()
                        if encoding is not None:
                            database.register_user(user_name, encoding)
                            user_registered = True
                            self.update_conversation_label(f"Usuário {user_name} registrado com sucesso.")
                            # Atualizar as listas de encodings e nomes
                            known_encodings = database.get_known_encodings()
                            known_users = database.get_user_names()
                            response = f"Muito prazer, {user_name}!"
                        else:
                            response = "Não consegui detectar seu rosto. Por favor, tente novamente."
                    else:
                        response = "Câmera não disponível para registrar o usuário."

                # Comando para verificar se a IA sabe o nome do usuário
                elif any(keyword in user_input_lower for keyword in NAME_QUERY_KEYWORDS):
                    if self.vision_assistant.camera_available:
                        index = self.vision_assistant.recognize_face(known_encodings)
                        if index is not None:
                            recognized_name = known_users[index]
                            response = f"Claro, você é {recognized_name}!"
                        else:
                            response = "Desculpe, não consegui reconhecê-lo."
                    else:
                        response = "Câmera não disponível para reconhecimento facial."

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

                # Perguntas sobre atributos faciais do usuário
                elif any(keyword in user_input_lower for keyword in USER_EMOTION_QUERY +
                                                              USER_AGE_QUERY +
                                                              USER_GENDER_QUERY +
                                                              USER_RACE_QUERY):
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
                                gender = attributes.get('gender', '')
                                if gender:
                                    response = f"Você parece ser do gênero {gender}."
                                else:
                                    response = "Desculpe, não consegui determinar seu gênero."

                            elif any(keyword in user_input_lower for keyword in USER_RACE_QUERY):
                                race = attributes.get('dominant_race', '')
                                if race:
                                    response = f"Você parece ser da raça {race}."
                                else:
                                    response = "Desculpe, não consegui determinar sua raça."
                        else:
                            response = "Desculpe, não consegui analisar seus atributos faciais. Certifique-se de que seu rosto está visível para a câmera."
                    else:
                        response = "Câmera não disponível para analisar atributos faciais."

                else:
                    # Obter resposta da IA
                    response = self.chatgpt.get_response(user_input, self.context)

            except Exception as e:
                print(f"Erro no fluxo de conversa: {e}")
                traceback.print_exc()
                response = "Desculpe, ocorreu um erro ao processar sua solicitação."

            self.update_conversation_label(f"Assistente: {response}")

            # Desativar a escuta enquanto a IA fala
            self.is_listening = False
            self.voice_assistant.speak(response)
            self.is_listening = True

            # Salvar conversa no banco de dados se o usuário for registrado
            if user_registered:
                database.save_conversation(user_name, user_input, response)

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

        # Campo para API Key
        self.api_key_label = QLabel("API Key do ChatGPT:")
        self.api_key_input = QLineEdit()
        self.api_key_input.setText(utils.get_setting("openai_api_key", ""))
        self.layout.addWidget(self.api_key_label)
        self.layout.addWidget(self.api_key_input)

        # Seleção de Microfone
        self.mic_label = QLabel("Dispositivo de Entrada de Áudio:")
        self.mic_selector = QComboBox()
        try:
            mic_list = utils.get_microphone_list()
            if not mic_list:
                mic_list = ["Nenhum dispositivo encontrado"]
            self.mic_selector.addItems(mic_list)
            self.mic_selector.setCurrentIndex(utils.get_setting("microphone_index", 0))
        except Exception as e:
            print(f"Erro ao obter a lista de microfones: {e}")
            traceback.print_exc()
            self.mic_selector.addItem("Erro ao carregar dispositivos")
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
            utils.set_setting("microphone_index", self.mic_selector.currentIndex())
            utils.set_setting("camera_index", self.cam_selector.currentIndex())
            utils.set_setting("camera_backend", self.backend_selector.currentText())

            QMessageBox.information(self, "Configurações Salvas", "As configurações foram salvas com sucesso.")
            self.close()
        except Exception as e:
            print(f"Erro ao salvar as configurações: {e}")
            traceback.print_exc()
            QMessageBox.critical(self, "Erro", "Ocorreu um erro ao salvar as configurações.")