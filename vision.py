# vision.py
import cv2
import numpy as np
import utils
import threading
import os
from deepface import DeepFace
import torch
from ultralytics import YOLO
import traceback

class VisionAssistant:
    def __init__(self):
        try:
            self.camera_index = utils.get_setting("camera_index", 0)
            self.camera_backend = utils.get_setting("camera_backend", "AUTO")
            self.camera_lock = threading.Lock()

            # Abrir a câmera uma vez
            backend = self.get_backend()
            self.cap = cv2.VideoCapture(self.camera_index, backend)
            self.camera_available = self.cap.isOpened()
            if not self.camera_available:
                print("Não foi possível abrir a câmera.")

            if self.camera_available:
                # Inicialize o modelo de detecção de objetos usando YOLO
                try:
                    self.device = "cuda" if torch.cuda.is_available() else "cpu"
                    # Atualizado para usar o modelo mais preciso
                    self.object_detector = YOLO('yolov8s.pt')

                    # Dicionário para tradução dos objetos
                    self.object_translation = {
                        'person': 'pessoa',
                        'bicycle': 'bicicleta',
                        'car': 'carro',
                        'motorcycle': 'moto',
                        'airplane': 'avião',
                        'bus': 'ônibus',
                        'train': 'trem',
                        'truck': 'caminhão',
                        'boat': 'barco',
                        'traffic light': 'semáforo',
                        'fire hydrant': 'hidrante',
                        'stop sign': 'placa de pare',
                        'parking meter': 'parquímetro',
                        'bench': 'banco',
                        'bird': 'pássaro',
                        'cat': 'gato',
                        'dog': 'cachorro',
                        'horse': 'cavalo',
                        'sheep': 'ovelha',
                        'cow': 'vaca',
                        'elephant': 'elefante',
                        'bear': 'urso',
                        'zebra': 'zebra',
                        'giraffe': 'girafa',
                        'backpack': 'mochila',
                        'umbrella': 'guarda-chuva',
                        'handbag': 'bolsa',
                        'tie': 'gravata',
                        'suitcase': 'mala',
                        'frisbee': 'frisbee',
                        'skis': 'esquis',
                        'snowboard': 'snowboard',
                        'sports ball': 'bola',
                        'kite': 'pipa',
                        'baseball bat': 'taco de beisebol',
                        'baseball glove': 'luva de beisebol',
                        'skateboard': 'skate',
                        'surfboard': 'prancha de surf',
                        'tennis racket': 'raquete de tênis',
                        'bottle': 'garrafa',
                        'wine glass': 'taça',
                        'cup': 'copo',
                        'fork': 'garfo',
                        'knife': 'faca',
                        'spoon': 'colher',
                        'bowl': 'tigela',
                        'banana': 'banana',
                        'apple': 'maçã',
                        'sandwich': 'sanduíche',
                        'orange': 'laranja',
                        'broccoli': 'brócolis',
                        'carrot': 'cenoura',
                        'hot dog': 'cachorro-quente',
                        'pizza': 'pizza',
                        'donut': 'rosquinha',
                        'cake': 'bolo',
                        'chair': 'cadeira',
                        'couch': 'sofá',
                        'potted plant': 'planta em vaso',
                        'bed': 'cama',
                        'dining table': 'mesa de jantar',
                        'toilet': 'vaso sanitário',
                        'tv': 'televisão',
                        'laptop': 'laptop',
                        'mouse': 'mouse',
                        'remote': 'controle remoto',
                        'keyboard': 'teclado',
                        'cell phone': 'celular',
                        'microwave': 'micro-ondas',
                        'oven': 'forno',
                        'toaster': 'torradeira',
                        'sink': 'pia',
                        'refrigerator': 'geladeira',
                        'book': 'livro',
                        'clock': 'relógio',
                        'vase': 'vaso',
                        'scissors': 'tesoura',
                        'teddy bear': 'ursinho de pelúcia',
                        'hair drier': 'secador de cabelo',
                        'toothbrush': 'escova de dentes',
                        # Objetos comuns na escola
                        'pen': 'caneta',
                        'pencil': 'lápis',
                        'notebook': 'caderno',
                        'lighter': 'isqueiro',
                        'mug': 'caneca',
                        'plate': 'prato',
                        'spoon': 'colher',
                        'fork': 'garfo',
                        'chair': 'cadeira',
                    }

                    # Dicionário para tradução das emoções
                    self.emotion_translation = {
                        'angry': 'raiva',
                        'disgust': 'desgosto',
                        'fear': 'medo',
                        'happy': 'feliz',
                        'sad': 'triste',
                        'surprise': 'surpreso',
                        'neutral': 'neutro'
                    }

                    # Dicionário para tradução de gênero
                    self.gender_translation = {
                        'Man': 'homem',
                        'Woman': 'mulher'
                    }

                    # Dicionário para tradução de etnia/raça
                    self.race_translation = {
                        'asian': 'asiático',
                        'indian': 'indiano',
                        'black': 'negro',
                        'white': 'branco',
                        'middle eastern': 'árabe',
                        'latino hispanic': 'hispânico'
                    }

                except Exception as e:
                    print(f"Erro ao carregar o modelo de detecção de objetos: {e}")
                    traceback.print_exc()
                    self.camera_available = False
            else:
                print("Nenhuma câmera disponível.")
        except Exception as e:
            print(f"Erro na inicialização do VisionAssistant: {e}")
            traceback.print_exc()

    def __del__(self):
        # Liberar a câmera quando o objeto for destruído
        if hasattr(self, 'cap') and self.cap.isOpened():
            self.cap.release()

    def get_backend(self):
        backend_options = {
            "AUTO": cv2.CAP_DSHOW if os.name == 'nt' else cv2.CAP_ANY,
            "CAP_DSHOW": cv2.CAP_DSHOW,
            "CAP_MSMF": cv2.CAP_MSMF,
            "CAP_V4L2": cv2.CAP_V4L2
        }
        backend = backend_options.get(self.camera_backend, cv2.CAP_ANY)
        return backend

    def capture_image(self):
        with self.camera_lock:
            if not self.cap.isOpened():
                print("Câmera não está aberta.")
                return None
            ret, frame = self.cap.read()
            if not ret or frame is None:
                print("Erro ao capturar a imagem da câmera.")
                return None
            # Verifique se a imagem tem 3 canais
            if len(frame.shape) == 3 and frame.shape[2] == 3:
                return frame
            else:
                print("Imagem capturada não está em formato RGB.")
                return None

    def recognize_object(self):
        if not self.camera_available:
            print("Câmera não disponível.")
            return None

        frame = self.capture_image()
        if frame is None:
            print("Imagem capturada é inválida.")
            return None

        try:
            results = self.object_detector(frame)
            if results:
                highest_confidence = 0
                best_object_name = None
                for result in results:
                    if result.boxes and len(result.boxes) > 0:
                        for box in result.boxes:
                            conf = box.conf.cpu().item()
                            if conf > highest_confidence:
                                highest_confidence = conf
                                class_id = int(box.cls.cpu().item())
                                object_name = result.names[class_id]
                                # Traduzir o nome do objeto para o português
                                object_name_pt = self.object_translation.get(object_name, object_name)
                                best_object_name = object_name_pt
                if best_object_name:
                    return best_object_name
            print("Nenhum objeto identificado.")
            return None
        except Exception as e:
            print(f"Erro ao reconhecer o objeto: {e}")
            traceback.print_exc()
            return None

    def analyze_face_attributes(self):
        if not self.camera_available:
            print("Câmera não disponível.")
            return None

        frame = self.capture_image()
        if frame is None:
            print("Imagem capturada é inválida.")
            return None

        try:
            # Converter a imagem para RGB
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            # Tentar usar vários backends para melhorar a detecção
            backends = ['opencv', 'mtcnn', 'ssd', 'dlib']
            for backend in backends:
                try:
                    # Analisar atributos faciais usando DeepFace com enforce_detection=False
                    result = DeepFace.analyze(
                        frame_rgb,
                        actions=['age', 'gender', 'emotion', 'race'],
                        detector_backend=backend,
                        enforce_detection=False
                    )
                    # Verificar se há rosto detectado
                    if result:
                        # Se o resultado for uma lista, pegar o primeiro elemento
                        if isinstance(result, list) and len(result) > 0:
                            result = result[0]
                        if isinstance(result, dict) and 'age' in result:
                            # Traduzir emoções
                            dominant_emotion = result.get('dominant_emotion', '')
                            if isinstance(dominant_emotion, str) and dominant_emotion in self.emotion_translation:
                                result['dominant_emotion'] = self.emotion_translation[dominant_emotion]
                            else:
                                print(f"dominant_emotion não é uma string ou não está no dicionário de tradução: {dominant_emotion}")

                            # Traduzir gênero usando 'dominant_gender'
                            dominant_gender = result.get('dominant_gender', '')
                            if isinstance(dominant_gender, str) and dominant_gender in self.gender_translation:
                                result['dominant_gender'] = self.gender_translation[dominant_gender]
                            else:
                                print(f"dominant_gender não é uma string ou não está no dicionário de tradução: {dominant_gender}")

                            # Traduzir etnia/raça
                            dominant_race = result.get('dominant_race', '')
                            if isinstance(dominant_race, str) and dominant_race in self.race_translation:
                                result['dominant_race'] = self.race_translation[dominant_race]
                            else:
                                print(f"dominant_race não é uma string ou não está no dicionário de tradução: {dominant_race}")

                            return result  # Retorna os resultados da análise
                except Exception as e:
                    print(f"Erro ao analisar atributos faciais com backend {backend}: {e}")
                    continue
            print("Nenhum rosto detectado para análise de atributos.")
            return None

        except Exception as e:
            print(f"Erro ao analisar atributos faciais: {e}")
            traceback.print_exc()
            return None