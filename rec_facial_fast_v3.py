
# -----------------------------------------------------------#
# Projeto   : Sistema de reconhecimento facial Rasberry      #
# File Name : recogintion_face_imagem_v6_final.py            #
# Data      : 16/09/2024                                     #
# Autor(a)s : Walner de Oliveira /                           #
# Objetivo  : executar em Webcam o reconhecimento facial     #
# Alteracao : 19/09/2024                                     #
#                                                            #
# arquivos desse sistema:                                    #
# rec_facial_fast_v3.py                                             #
# main.py                                                    #
# ativar_gpio.py                                             #
# -----------------------------------------------------------#
#USO

#python rec_facial_fast_v3.py

#KILL
#ps aux | grep python
#kill -9 <proc>
#kill -9 2439
import face_recognition
import pickle
import cv2
import os
import subprocess
import threading
from queue import Queue, Empty

# Função para ativar a GPIO com base no 'item' usando subprocess
def activate_gpio(item):
    subprocess.run(['sudo', 'python3', 'ativar_gpio.py', str(item)], check=True)

# Função para tocar o áudio usando mpg123
def play_audio(audio_path):
    if os.path.exists(audio_path):
        subprocess.run(['mpg123', audio_path], check=True)

# Função para carregar as codificações faciais do arquivo pickle
def load_encodings(pickle_file):
    with open(pickle_file, 'rb') as f:
        data = pickle.load(f)
    return data['users']

# Função para reconhecimento facial (codificação e comparação)
def recognize_faces(face_queue, users, frames_without_recognition, forget_frames):
    while True:
        try:
            frame_data = face_queue.get(timeout=1)
            if frame_data is None:
                break
        except Empty:
            continue

        frame, boxes, resize_scale = frame_data
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        encodings = face_recognition.face_encodings(rgb_frame, boxes)
        current_frame_names = set()

        for encoding in encodings:
            name = "Unknown"
            for user in users:
                matches = face_recognition.compare_faces(user['encodings'], encoding, tolerance=0.5)
                if True in matches:
                    name = user['name']
                    break

            if name != "Unknown":
                print(f"Pessoa reconhecida: {name}")
                current_frame_names.add(name)

                # Se o nome for reconhecido, zerar o contador de frames sem reconhecimento
                frames_without_recognition[0] = 0

                user = next(user for user in users if user['name'] == name)
                audio_path = os.path.join('/home/felipe/static/audio', user['audio'])

                # Tocar o áudio e ativar o GPIO
                threading.Thread(target=play_audio, args=(audio_path,)).start()
                threading.Thread(target=activate_gpio, args=(user['item'],)).start()

        # Se nenhum nome foi reconhecido neste frame, aumentar o contador
        if not current_frame_names:
            frames_without_recognition[0] += 1
            print(f"Nenhum nome reconhecido por {frames_without_recognition[0]} frames.")

        # Se atingiu o número de frames sem reconhecimento, acionar GPIO e áudio novamente
        if frames_without_recognition[0] >= forget_frames:
            print(f"Passaram-se {forget_frames} frames sem reconhecer nenhum nome, acionando novamente.")
            frames_without_recognition[0] = 0  # Resetar o contador após acionar

        face_queue.task_done()

# Função para detectar faces e colocar na fila
def detect_faces(encodings_file, frame_skip=10, resize_scale=0.7, forget_frames=15):
    users = load_encodings(encodings_file)

    if not users:
        print("Nenhum usuário encontrado no arquivo de codificações.")
        return

    face_queue = Queue()
    frames_without_recognition = [0]  # Usar lista para rastrear frames sem reconhecimento

    recognize_thread = threading.Thread(target=recognize_faces, args=(face_queue, users, frames_without_recognition, forget_frames))
    recognize_thread.start()

    video_capture = cv2.VideoCapture(0)
    frame_count = 0

    if not video_capture.isOpened():
        print("Falha ao abrir a webcam.")
        return

    while True:
        ret, frame = video_capture.read()
        if not ret:
            print("Falha ao capturar frame da webcam.")
            break

        if frame_count % frame_skip != 0:
            frame_count += 1
            continue

        frame_count += 1
        small_frame = cv2.resize(frame, (0, 0), fx=resize_scale, fy=resize_scale)
        rgb_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)

        # Detecção de faces
        boxes = face_recognition.face_locations(rgb_frame, model="hog")

        if boxes:
            face_queue.put((small_frame, boxes, resize_scale))

        for (top, right, bottom, left) in boxes:
            top = int(top / resize_scale)
            right = int(right / resize_scale)
            bottom = int(bottom / resize_scale)
            left = int(left / resize_scale)

            cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 2)

    face_queue.put(None)
    face_queue.join()
    recognize_thread.join()

    video_capture.release()

# Caminho para o arquivo pickle com as codificações faciais
encodings_file = '/home/felipe/encodings.pkl'

# Inicia a detecção e reconhecimento facial
detect_faces(encodings_file, frame_skip=20, resize_scale=0.5)
