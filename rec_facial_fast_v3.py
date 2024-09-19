import face_recognition
import pickle
import cv2
import os
import subprocess
from queue import Queue, Empty
import signal
import sys

# Variável global para sinalizar o término do processo
stop_processing = False


# Função para ativar a GPIO com base no 'item' usando subprocess
def activate_gpio(item):
    subprocess.run(['sudo', 'python3', 'ativar_gpio.py', str(item)])


# Função para tocar o áudio usando mpg123
def play_audio(audio_path):
    if os.path.exists(audio_path):
        subprocess.run(['mpg123', audio_path])


# Função para carregar as codificações faciais do arquivo pickle
def load_encodings(pickle_file):
    with open(pickle_file, 'rb') as f:
        data = pickle.load(f)
    return data['users']


# Função para reconhecimento facial (codificação e comparação)
def recognize_faces(face_queue, users, played_audios, last_seen, forget_frames):
    while not stop_processing:
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
                current_frame_names.add(name)

                if last_seen.get(name, 0) <= 0:
                    if name not in played_audios:
                        user = next(user for user in users if user['name'] == name)
                        audio_path = os.path.join('/home/felipe/static/audio', user['audio'])
                        play_audio(audio_path)
                        activate_gpio(user['item'])

                last_seen[name] = forget_frames

        for name in last_seen.keys():
            if name not in current_frame_names:
                last_seen[name] -= 1

        face_queue.task_done()


# Função para detectar faces e colocar na fila
def detect_faces(encodings_file, frame_skip=10, resize_scale=0.7, forget_frames=5):
    global stop_processing
    users = load_encodings(encodings_file)

    if not users:
        return

    played_audios = set()
    face_queue = Queue()
    last_seen = {}

    video_capture = cv2.VideoCapture(0)
    frame_count = 0

    if not video_capture.isOpened():
        return

    try:
        while not stop_processing:
            ret, frame = video_capture.read()
            if not ret:
                break

            if frame_count % frame_skip != 0:
                frame_count += 1
                continue

            frame_count += 1
            small_frame = cv2.resize(frame, (0, 0), fx=resize_scale, fy=resize_scale)
            rgb_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)

            boxes = face_recognition.face_locations(rgb_frame, model="hog")

            if boxes:
                face_queue.put((small_frame, boxes, resize_scale))

        face_queue.put(None)
        face_queue.join()

    finally:
        video_capture.release()


# Função para capturar o sinal de interrupção (Ctrl + C)
def signal_handler(sig, frame):
    global stop_processing
    stop_processing = True
    sys.exit(0)


signal.signal(signal.SIGINT, signal_handler)

encodings_file = '/home/felipe/encodings.pkl'

# Inicia a detecção e reconhecimento facial com threads separadas
detect_faces(encodings_file, frame_skip=20, resize_scale=0.5)
