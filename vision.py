# vision.py
import cv2
import numpy as np
import utils
import threading
from deepface import DeepFace
from sklearn.metrics.pairwise import cosine_similarity
import torch
from ultralytics import YOLO
import traceback

class VisionAssistant:
    def __init__(self):
        try:
            self.camera_index = utils.get_setting("camera_index", 0)
            self.camera_backend = utils.get_setting("camera_backend", "AUTO")
            self.camera_available = self.check_camera()
            self.camera_lock = threading.Lock()

            # Pré-carregar modelos para reduzir o tempo de resposta
            self.face_recognition_model = 'Facenet'  # Pode testar com 'VGG-Face' ou 'OpenFace'
            self.face_analysis_models = {}  # Cache para modelos de análise facial

            if self.camera_available:
                # Inicialize o modelo de detecção de objetos usando YOLO
                try:
                    self.device = "cuda" if torch.cuda.is_available() else "cpu"
                    self.object_detector = YOLO('yolov8n.pt')
                except Exception as e:
                    print(f"Erro ao carregar o modelo de detecção de objetos: {e}")
                    traceback.print_exc()
                    self.camera_available = False
            else:
                print("Nenhuma câmera disponível.")
        except Exception as e:
            print(f"Erro na inicialização do VisionAssistant: {e}")
            traceback.print_exc()

    def get_backend(self):
        backend_options = {
            "AUTO": cv2.CAP_ANY,
            "CAP_DSHOW": cv2.CAP_DSHOW,
            "CAP_MSMF": cv2.CAP_MSMF,
            "CAP_V4L2": cv2.CAP_V4L2
        }
        backend = backend_options.get(self.camera_backend, cv2.CAP_ANY)
        return backend

    def check_camera(self):
        backend = self.get_backend()
        cap = cv2.VideoCapture(self.camera_index, backend)
        result = cap.isOpened()
        cap.release()
        return result

    def capture_image(self):
        with self.camera_lock:
            backend = self.get_backend()
            for _ in range(3):
                cap = cv2.VideoCapture(self.camera_index, backend)
                if not cap.isOpened():
                    cap.release()
                    continue
                # Definir resolução da câmera
                cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
                cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
                ret, frame = cap.read()
                cap.release()
                if ret and frame is not None and np.sum(frame) > 0:
                    # Verifique se a imagem tem 3 canais
                    if len(frame.shape) == 3 and frame.shape[2] == 3:
                        return frame
                    else:
                        print("Imagem capturada não está em formato RGB.")
                else:
                    continue
            print("Não foi possível capturar a imagem após múltiplas tentativas")
            return None

    def encode_face(self):
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
            # Usando o DeepFace para representar a face com enforce_detection=False
            result = DeepFace.represent(frame_rgb, model_name=self.face_recognition_model, detector_backend='mtcnn', enforce_detection=False)
            if result and len(result) > 0:
                return result[0]['embedding']  # Retorna a representação da primeira face detectada
            else:
                print("Nenhum rosto detectado.")
        except Exception as e:
            print(f"Erro ao calcular as codificações faciais: {e}")
            traceback.print_exc()
        return None

    def recognize_face(self, known_encodings):
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
            # Representa a face atual com enforce_detection=False
            result = DeepFace.represent(frame_rgb, model_name=self.face_recognition_model, detector_backend='mtcnn', enforce_detection=False)
            if result and len(result) > 0:
                captured_embedding = result[0]['embedding']

                # Comparar com as codificações conhecidas
                captured_embedding = np.array(captured_embedding).reshape(1, -1)
                for idx, known_encoding in enumerate(known_encodings):
                    known_embedding = np.array(known_encoding).reshape(1, -1)
                    similarity = cosine_similarity(captured_embedding, known_embedding)[0][0]
                    if similarity >= 0.7:  # Ajuste o limiar conforme necessário
                        return idx
            else:
                print("Nenhum rosto detectado.")
        except Exception as e:
            print(f"Erro ao reconhecer a face: {e}")
            traceback.print_exc()
        print("Nenhum rosto reconhecido.")
        return None

    def find_matching_encoding(self, encoding, known_encodings):
        # encoding é um array numpy de shape (embedding_size,)
        encoding = np.array(encoding).reshape(1, -1)
        for idx, known_encoding in enumerate(known_encodings):
            known_embedding = np.array(known_encoding).reshape(1, -1)
            similarity = cosine_similarity(encoding, known_embedding)[0][0]
            if similarity >= 0.7:  # Ajuste o limiar conforme necessário
                return idx  # Retorna o índice da codificação correspondente
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
                for result in results:
                    if result.boxes and len(result.boxes) > 0:
                        # Obter o nome do objeto com maior confiança
                        class_id = int(result.boxes.cls[0])
                        object_name = result.names[class_id]
                        return object_name
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
            backends = ['mtcnn', 'opencv', 'ssd', 'dlib']
            for backend in backends:
                try:
                    # Analisar atributos faciais usando DeepFace com enforce_detection=False
                    result = DeepFace.analyze(frame_rgb, actions=['age', 'gender', 'emotion', 'race'],
                                              detector_backend=backend, enforce_detection=False)
                    # Verificar se há rosto detectado
                    if result:
                        # Se o resultado for uma lista, pegar o primeiro elemento
                        if isinstance(result, list) and len(result) > 0:
                            result = result[0]
                        if isinstance(result, dict) and 'age' in result:
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