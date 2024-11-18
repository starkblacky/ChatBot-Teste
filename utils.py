import json
import os
import cv2
import traceback
import sounddevice as sd

SETTINGS_FILE = 'settings.json'

def get_setting(key, default=None):
    try:
        if os.path.exists(SETTINGS_FILE):
            with open(SETTINGS_FILE, 'r') as f:
                settings = json.load(f)
                return settings.get(key, default)
        else:
            return default
    except Exception as e:
        print(f"Erro ao carregar a configuração {key}: {e}")
        traceback.print_exc()
        return default

def set_setting(key, value):
    try:
        settings = {}
        if os.path.exists(SETTINGS_FILE):
            with open(SETTINGS_FILE, 'r') as f:
                settings = json.load(f)
        settings[key] = value
        with open(SETTINGS_FILE, 'w') as f:
            json.dump(settings, f, indent=4)
    except Exception as e:
        print(f"Erro ao salvar a configuração {key}: {e}")
        traceback.print_exc()

def get_microphone_list():
    mic_list = []
    try:
        devices = sd.query_devices()
        for index, dev in enumerate(devices):
            if dev['max_input_channels'] > 0:
                mic_list.append({'index': index, 'name': dev['name']})
    except Exception as e:
        print(f"Erro ao listar microfones: {e}")
        traceback.print_exc()
    return mic_list

def get_camera_list():
    index = 0
    arr = []
    while True:
        cap = cv2.VideoCapture(index)
        if not cap.read()[0]:
            break
        else:
            arr.append(f"Câmera {index}")
        cap.release()
        index +=1
    return arr if arr else ["Nenhuma câmera detectada"]

def get_backend_list():
    backends = ["AUTO"]
    if hasattr(cv2, 'CAP_DSHOW'):
        backends.append("CAP_DSHOW")
    if hasattr(cv2, 'CAP_MSMF'):
        backends.append("CAP_MSMF")
    if hasattr(cv2, 'CAP_V4L2'):
        backends.append("CAP_V4L2")
    return backends