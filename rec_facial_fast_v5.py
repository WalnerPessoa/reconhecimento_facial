

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
import time  # Biblioteca para medir o tempo


# Lock para sincronizar o acesso ao GPIO. Isso impede que duas threads tentem ativar o GPIO ao mesmo tempo.
gpio_lock = threading.Lock()

# Marca o tempo de início do código
start_time = time.time()

# Função responsável por ativar um GPIO específico. O 'item' determina qual pino será ativado.
def activate_gpio(item):
    with gpio_lock:  # Garante que apenas uma thread por vez execute essa função.
        subprocess.run(['sudo', 'python3', '/home/felipe/ativar_gpio.py', str(item)], check=True)

# Função para tocar um arquivo de áudio usando o player 'mpg123'.
def play_audio(audio_path):
    if os.path.exists(audio_path):  # Verifica se o arquivo de áudio existe.
        subprocess.run(['/usr/bin/mpg123', audio_path], check=True)

# Função que carrega as codificações faciais dos usuários salvas em um arquivo pickle.
def load_encodings(pickle_file):
    with open(pickle_file, 'rb') as f:
        data = pickle.load(f)  # Carrega o arquivo pickle com os dados dos usuários.
    return data['users']  # Retorna as codificações faciais dos usuários.

# Função que realiza o reconhecimento facial.
# Utiliza uma fila (queue) para processar os frames capturados pela webcam.
def recognize_faces(face_queue, users, played_audios, frames_without_recognition, forget_frames):
    first_detection = False  # Flag para identificar a primeira detecção
    if not first_detection:  # Checa se é a primeira detecção
        first_detection = True
        detection_time = time.time() - start_time  # Calcula o tempo até a primeira detecção
        print(f"Tempo de primeiro reconhecimento de rosto...: {detection_time:.2f} segundos")
    while True:
        try:
            frame_data = face_queue.get(timeout=1)  # Tenta pegar um frame da fila, aguardando até 1 segundo.
            if frame_data is None:  # Condição para sair do loop.
                break
        except Empty:  # Se a fila estiver vazia, continua o loop até que um frame esteja disponível.
            continue

        # Desempacotando os dados do frame
        frame, boxes, resize_scale = frame_data
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)  # Converte o frame para o formato RGB.

        # Obtém as codificações faciais para cada rosto detectado no frame.
        encodings = face_recognition.face_encodings(rgb_frame, boxes)

        current_frame_names = set()  # Um conjunto para rastrear os nomes das pessoas reconhecidas no frame atual.

        # Compara as codificações faciais encontradas com as dos usuários cadastrados.
        for encoding in encodings:
            name = "Unknown"  # Se não for encontrada uma correspondência, o nome será "Unknown".
            for user in users:
                matches = face_recognition.compare_faces(user['encodings'], encoding, tolerance=0.5)
                if True in matches:
                    name = user['name']  # Nome do usuário reconhecido.
                    break

            if name != "Unknown":  # Se um rosto foi reconhecido...
                print(f"Pessoa reconhecida: {name}")
                current_frame_names.add(name)  # Adiciona o nome da pessoa reconhecida ao conjunto.

                # Zera o contador de frames sem reconhecimento.
                frames_without_recognition[0] = 0

                # Toca o áudio e ativa o GPIO apenas uma vez por nome reconhecido.
                if name not in played_audios:
                    user = next(user for user in users if user['name'] == name)
                    audio_path = os.path.join('/home/felipe/static/audio', user['audio'])

                    # Inicia uma thread para tocar o áudio.
                    audio_thread = threading.Thread(target=play_audio, args=(audio_path,))
                    audio_thread.daemon = True  # Definir como thread daemon.
                    audio_thread.start()

                    # Inicia uma thread para ativar o GPIO.
                    gpio_thread = threading.Thread(target=activate_gpio, args=(user['item'],))
                    gpio_thread.daemon = True  # Definir como thread daemon.
                    gpio_thread.start()

                    # Marca o nome como já acionado.
                    played_audios.add(name)

        # Se nenhum nome foi reconhecido no frame atual, aumenta o contador.
        if not current_frame_names:
            frames_without_recognition[0] += 1
            print(f"Nenhum nome reconhecido por {frames_without_recognition[0]} frames.")

        # Se não houver reconhecimento por um número suficiente de frames, reseta os nomes acionados.
        if frames_without_recognition[0] >= forget_frames:
            print(f"Passaram-se {forget_frames} frames sem reconhecer nenhum nome, resetando estado.")
            frames_without_recognition[0] = 0
            played_audios.clear()  # Esquece todos os nomes, permitindo que sejam acionados novamente.

        face_queue.task_done()  # Indica que o processamento do frame foi concluído.

# Função que captura os frames da webcam e detecta rostos.
def detect_faces(encodings_file, frame_skip=10, resize_scale=0.7, forget_frames=28, model_detection="hog"):
    first_detection = False  # Flag para identificar a primeira detecção
    last_mtime = os.path.getmtime(encodings_file)  # Obter o timestamp inicial do arquivo

    # Carrega as codificações faciais dos usuários cadastrados.
    users = load_encodings(encodings_file)
    print("[INFO] Carregando codificações faciais dos usuários cadastrados...")

    if not users:  # Se não houver usuários cadastrados, encerra a função.
        print("Nenhum usuário cadastrado no arquivo de codificações.")
        return

    # Fila de processamento dos frames.
    face_queue = Queue()
    played_audios = set()  # Armazena os nomes dos usuários que já tiveram seu áudio tocado.
    frames_without_recognition = [0]  # Contador de frames sem reconhecimento.

    # Inicia uma thread para o reconhecimento facial em paralelo à captura de frames.
    recognize_thread = threading.Thread(target=recognize_faces, args=(face_queue, users, played_audios, frames_without_recognition, forget_frames))
    recognize_thread.start()

    # Abertura da webcam.
    video_capture = cv2.VideoCapture(0)
    frame_count = 0

    if not video_capture.isOpened():  # Verifica se a webcam foi aberta corretamente.
        print("Falha ao abrir a webcam.")
        return

    # Loop de captura de frames da webcam.
    while True:
        ret, frame = video_capture.read()  # Captura um frame.
        if not ret:
            print("Falha ao capturar frame da webcam.")
            break

        if frame_count % frame_skip != 0:  # Pula frames para economizar processamento.
            frame_count += 1
            continue

        frame_count += 1

        # Verifica se o arquivo de codificações foi modificado
        current_mtime = os.path.getmtime(encodings_file)
        if current_mtime > last_mtime:  # Se o arquivo foi modificado
            print("[INFO] Atualizando codificações faciais...")
            users = load_encodings(encodings_file)  # Recarrega as codificações
            last_mtime = current_mtime  # Atualiza o timestamp

        small_frame = cv2.resize(frame, (0, 0), fx=resize_scale, fy=resize_scale)  # Redimensiona o frame.
        rgb_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)  # Converte o frame para RGB.

        # Detecta as localizações dos rostos no frame.
        boxes = face_recognition.face_locations(rgb_frame, model=model_detection)
        if not first_detection:  # Checa se é a primeira detecção
            first_detection = True
            detection_time = time.time() - start_time  # Calcula o tempo até a primeira detecção
            print(f"Tempo de primeira detecção de rosto...: {detection_time:.2f} segundos")

        if not boxes:
            frames_without_recognition[0] = 0
            print('[ACTION] Permitir que usuários sejam reconhecidos novamente')
            played_audios.clear()  # Esquece todos os nomes, permitindo que sejam acionados novamente.

        if boxes:  # Se forem detectadas faces, coloca o frame na fila.
            face_queue.put((small_frame, boxes, resize_scale))

        # Desenha um retângulo ao redor de cada face detectada.
        for (top, right, bottom, left) in boxes:
            top = int(top / resize_scale)
            right = int(right / resize_scale)
            bottom = int(bottom / resize_scale)
            left = int(left / resize_scale)

            cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 2)

    face_queue.put(None)  # Envia um sinal para finalizar a thread de reconhecimento.
    face_queue.join()  # Aguarda todas as tarefas na fila serem concluídas.
    recognize_thread.join()  # Aguarda a finalização da thread de reconhecimento.

    video_capture.release()  # Libera a câmera.

# Caminho para o arquivo pickle com as codificações faciais.
encodings_file = '/home/felipe/encodings.pkl'

# Inicia a detecção e reconhecimento facial.
detect_faces(encodings_file, frame_skip=20, resize_scale=0.5, forget_frames=28, model_detection="hog")
