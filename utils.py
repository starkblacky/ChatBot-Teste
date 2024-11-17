# utils.py
import json
import os
import speech_recognition as sr
import cv2

SETTINGS_FILE = 'settings.json'

def get_setting(key, default=None):
    if os.path.exists(SETTINGS_FILE):
        with open(SETTINGS_FILE, 'r') as f:
            settings = json.load(f)
            return settings.get(key, default)
    return default

def set_setting(key, value):
    settings = {}
    if os.path.exists(SETTINGS_FILE):
        with open(SETTINGS_FILE, 'r') as f:
            settings = json.load(f)
    settings[key] = value
    with open(SETTINGS_FILE, 'w') as f:
        json.dump(settings, f, indent=4)

def get_microphone_list():
    """
    Esta função obtém a lista de microfones disponíveis e seus respectivos índices.

    Retorna:
    list: Lista de strings, onde cada string representa um microfone no formato "index: name".
    """
    mic_list = []
    for index, name in enumerate(sr.Microphone.list_microphone_names()):
        mic_list.append(f"{index}: {name}")
    return mic_list

def get_camera_list():
    index = 0
    arr = []
    while True:
        cap = cv2.VideoCapture(index, cv2.CAP_DSHOW)
        if not cap.isOpened():
            cap.release()
            break
        else:
            arr.append(f"Câmera {index}")
        cap.release()
        index += 1
    return arr if arr else ["Nenhuma câmera detectada"]

def get_backend_list():
    """
    Retorna uma lista de backends de câmera disponíveis.
    """
    backends = ["AUTO"]
    if hasattr(cv2, 'CAP_DSHOW'):
        backends.append("CAP_DSHOW")
    if hasattr(cv2, 'CAP_MSMF'):
        backends.append("CAP_MSMF")
    if hasattr(cv2, 'CAP_V4L2'):
        backends.append("CAP_V4L2")
    return backends