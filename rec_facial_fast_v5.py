

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
import time

# Lock para sincronizar o acesso ao GPIO e ao carregamento de codificações.
gpio_lock = threading.Lock()
encodings_lock = threading.Lock()  # Lock para sincronizar o acesso à variável 'users'

# Função responsável por ativar um GPIO específico.
def activate_gpio(item):
    with gpio_lock:
        subprocess.run(['sudo', 'python3', '/home/felipe/ativar_gpio.py', str(item)], check=True)

# Função para tocar um arquivo de áudio usando o player 'mpg123'.
#def play_audio(audio_path):
#    if os.path.exists(audio_path):
#        subprocess.run(['/usr/bin/mpg123', audio_path], check=True)



def play_audio(audio_path):
    #time.sleep(2)  # Aguarda 5 segundos para garantir que os serviços de áudio estejam disponíveis
    if os.path.exists(audio_path):
        try:
            subprocess.run(['mpg123', audio_path], check=True)
        except subprocess.CalledProcessError as e:
            print(f"Erro ao tocar áudio: {e}")
    else:
        print(f"Arquivo de áudio {audio_path} não encontrado.")

         
#def play_audio(audio_path):
#    if os.path.exists(audio_path):
#        try:
#            subprocess.run(['/usr/bin/mpg123', audio_path], check=True)
#        except subprocess.CalledProcessError as e:
#            print(f"Erro ao tocar áudio: {e}")
#    else:
#        print(f"Arquivo de áudio {audio_path} não encontrado.")


# Função que carrega as codificações faciais dos usuários salvas em um arquivo pickle.

def load_encodings(pickle_file):
    with encodings_lock:  # Garantir que o acesso seja controlado ao carregar as codificações.
        with open(pickle_file, 'rb') as f:
            data = pickle.load(f)
    print(f"[INFO ENCODING] Encodings carregados: {data['users']}")  # Adicione isso para verificar o carregamento
    return data['users']



# Função que realiza o reconhecimento facial.
def recognize_faces(face_queue, users, played_audios, frames_without_recognition, forget_frames):
    first_detection = False
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
            with encodings_lock:  # Garantir que o acesso ao 'users' seja sincronizado.
                for user in users:
                    matches = face_recognition.compare_faces(user['encodings'], encoding, tolerance=0.5)
                    if True in matches:
                        name = user['name']
                        break

            if name != "Unknown":
                print(f"Pessoa reconhecida: {name}")
                current_frame_names.add(name)
                frames_without_recognition[0] = 0

                if name not in played_audios:
                    user = next(user for user in users if user['name'] == name)
                    audio_path = os.path.join('/home/felipe/static/audio', user['audio'])

                    audio_thread = threading.Thread(target=play_audio, args=(audio_path,))
                    audio_thread.daemon = True
                    audio_thread.start()

                    gpio_thread = threading.Thread(target=activate_gpio, args=(user['item'],))
                    gpio_thread.daemon = True
                    gpio_thread.start()

                    played_audios.add(name)

        if not current_frame_names:
            frames_without_recognition[0] += 1
            #print(f"Nenhum nome reconhecido por {frames_without_recognition[0]} frames.")

        if frames_without_recognition[0] >= forget_frames:
            #print(f"Passaram-se {forget_frames} frames sem reconhecer nenhum nome, resetando estado.")
            frames_without_recognition[0] = 0
            played_audios.clear()

        face_queue.task_done()

# Função para verificar se o arquivo de codificações foi modificado.
def check_for_new_encodings(encodings_file, last_mtime):
    current_mtime = os.path.getmtime(encodings_file)

    if current_mtime > last_mtime:
        print("[INFO] Atualizando codificações faciais... Reiniciando o serviço.")
        try:
            result = subprocess.run(['sudo', 'systemctl', 'restart', 'rec_facial.service'], check=True)
            if result.returncode == 0:
                print("[INFO] Serviço reiniciado com sucesso.")
            else:
                print(f"[ERRO] Falha ao reiniciar o serviço. Código de saída: {result.returncode}")
        except subprocess.CalledProcessError as e:
            print(f"[ERRO] Falha ao reiniciar o serviço: {e}")

    return current_mtime

#def check_for_new_encodings(encodings_file, last_mtime):
#    current_mtime = os.path.getmtime(encodings_file)#

#    if current_mtime > last_mtime:
#        print("[INFO] Atualizando codificações faciais... Reiniciando o serviço.")
#        try:
#            subprocess.run(['sudo', 'systemctl', 'restart', 'rec_facial.service'], check=True)
#            print("[INFO] Serviço reiniciado com sucesso.")
#        except subprocess.CalledProcessError as e:
#            print(f"[ERRO] Falha ao reiniciar o serviço: {e}")
#
#    return current_mtime


# Função que captura os frames da webcam e detecta rostos.
def detect_faces(encodings_file, check_interval=10, resize_scale=0.7, forget_frames=28, model_detection="hog"):
    users = load_encodings(encodings_file)
    last_mtime = os.path.getmtime(encodings_file)
    print("[INFO] Codificações faciais carregadas inicialmente.")

    face_queue = Queue()
    played_audios = set()
    frames_without_recognition = [0]

    recognize_thread = threading.Thread(target=recognize_faces, args=(face_queue, users, played_audios, frames_without_recognition, forget_frames))
    recognize_thread.start()

    video_capture = cv2.VideoCapture(0)
    if not video_capture.isOpened():
        print("Falha ao abrir a webcam.")
        return

    last_check_time = time.time()

    while True:
        ret, frame = video_capture.read()
        if not ret:
            print("Falha ao capturar frame da webcam.")
            break

        small_frame = cv2.resize(frame, (0, 0), fx=resize_scale, fy=resize_scale)
        rgb_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)
        boxes = face_recognition.face_locations(rgb_frame, model=model_detection)

        if not boxes:
            frames_without_recognition[0] = 0
            #print('[ACTION] Permitir que usuários sejam reconhecidos novamente')
            played_audios.clear()  # Esquece todos os nomes, permitindo que sejam acionados novamente.

        if boxes:
            face_queue.put((small_frame, boxes, resize_scale))

        # Verificação independente da modificação do arquivo de codificações.
        current_time = time.time()
        if current_time - last_check_time >= check_interval:
            last_mtime = check_for_new_encodings(encodings_file, last_mtime)
            last_check_time = current_time

    face_queue.put(None)
    face_queue.join()
    recognize_thread.join()
    video_capture.release()

# Caminho para o arquivo pickle com as codificações faciais.
encodings_file = '/home/felipe/encodings.pkl'

# Inicia a detecção e reconhecimento facial.
detect_faces(encodings_file, check_interval=10, resize_scale=0.5, forget_frames=28, model_detection="hog")
