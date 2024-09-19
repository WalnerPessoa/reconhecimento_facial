
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


import face_recognition
import pickle
import cv2
import os
import subprocess
import threading
from queue import Queue, Empty
import signal
import sys

# Variável global para sinalizar o término do processo
stop_processing = False

# Função para ativar a GPIO com base no 'item' usando subprocess
def activate_gpio(item):
    try:
        subprocess.run(['sudo', 'python3', 'ativar_gpio.py', str(item)], check=True)
        print(f"GPIO {item} ativada com sucesso.")
    except subprocess.CalledProcessError as e:
        print(f"Erro ao ativar a GPIO {item}: {e}")

# Função para tocar o áudio usando mpg123
def play_audio(audio_path):
    try:
        if os.path.exists(audio_path):
            subprocess.run(['mpg123', audio_path], check=True)
        else:
            print(f"Arquivo de áudio não encontrado: {audio_path}")
    except Exception as e:
        print(f"Erro ao tocar o áudio: {e}")

# Função para carregar as codificações faciais do arquivo pickle
def load_encodings(pickle_file):
    try:
        with open(pickle_file, 'rb') as f:
            data = pickle.load(f)
        return data['users']
    except FileNotFoundError:
        print(f"Arquivo {pickle_file} não encontrado.")
        return []
    except Exception as e:
        print(f"Erro ao carregar o arquivo pickle: {e}")
        return []

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
        current_frame_names = set()  # Nomes reconhecidos no frame atual
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

                # Verifica se o nome sumiu nos últimos `forget_frames` quadros
                if last_seen.get(name, 0) <= 0:  # Nome não foi visto nos últimos frames
                    user = next(user for user in users if user['name'] == name)
                    audio_path = os.path.join('/home/felipe/static/audio', user['audio'])
                    gpio_audio_thread = threading.Thread(target=play_audio, args=(audio_path,))
                    gpio_audio_thread.start()
                    activate_gpio(user['item'])

                last_seen[name] = forget_frames  # Reinicia o contador para o nome

        # Atualiza o contador para os nomes não vistos neste frame
        for name in list(last_seen.keys()):
            if name not in current_frame_names:
                last_seen[name] -= 1
                if last_seen[name] <= 0:
                    del last_seen[name]  # Remove o nome se ele sumiu por tempo suficiente

        face_queue.task_done()

# Função para detectar faces e colocar na fila
def detect_faces(encodings_file, frame_skip=10, resize_scale=0.7, forget_frames=3):
    global stop_processing
    print("[INFO] Carregando codificações faciais...")
    users = load_encodings(encodings_file)

    if not users:
        print("Nenhum usuário encontrado no arquivo de codificações.")
        return

    played_audios = set()
    face_queue = Queue()
    last_seen = {}  # Dicionário para armazenar o tempo desde que o nome foi visto

    recognize_thread = threading.Thread(target=recognize_faces, args=(face_queue, users, played_audios, last_seen, forget_frames))
    recognize_thread.start()

    video_capture = cv2.VideoCapture(0)
    frame_count = 0

    if not video_capture.isOpened():
        print("Falha ao abrir a webcam.")
        return

    try:
        while not stop_processing:
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

            # Desenhar as caixas ao redor das faces
            for (top, right, bottom, left) in boxes:
                top = int(top / resize_scale)
                right = int(right / resize_scale)
                bottom = int(bottom / resize_scale)
                left = int(left / resize_scale)

                cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 2)

            #cv2.imshow("Webcam - Detecção Facial", frame)

            #if cv2.waitKey(1) & 0xFF == ord('q'):
            #    break
    except KeyboardInterrupt:
        print("\n[INFO] Interrupção detectada, finalizando...")
        stop_processing = True
    finally:
        face_queue.put(None)
        face_queue.join()
        recognize_thread.join()

        video_capture.release()
        #cv2.destroyAllWindows()

# Função para capturar o sinal de interrupção (Ctrl + C)
def signal_handler(sig, frame):
    global stop_processing
    print("\n[INFO] Interrupção detectada, finalizando...")
    stop_processing = True
    sys.exit(0)

# Configurar o sinal de interrupção para capturar Ctrl + C
signal.signal(signal.SIGINT, signal_handler)

# Caminho para o arquivo pickle com as codificações faciais
encodings_file = '/home/felipe/encodings.pkl'

# Inicia a detecção e reconhecimento facial com threads separadas
detect_faces(encodings_file, frame_skip=20, resize_scale=0.5)
