import face_recognition
import pickle
import cv2
import pygame
import os
import subprocess


# Função para ativar a GPIO com base no 'item' usando subprocess
def activate_gpio(item):
    try:
        subprocess.run(['sudo', 'python3', '/home/felipe/ativar_gpio.py', str(item)], check=True)
        print(f"GPIO {item} ativada com sucesso.")
    except subprocess.CalledProcessError as e:
        print(f"Erro ao ativar a GPIO {item}: {e}")


# Inicializar o mixer do pygame e definir múltiplos canais
pygame.mixer.init()
pygame.mixer.set_num_channels(8)  # Permite até 8 canais de áudio simultâneos


# Função para tocar o áudio usando pygame em um canal específico
def play_audio(audio_path):
    try:
        if os.path.exists(audio_path):  # Verificar se o arquivo existe
            channel = pygame.mixer.find_channel()  # Encontra um canal livre
            if channel is not None:
                sound = pygame.mixer.Sound(audio_path)  # Carrega o som
                channel.play(sound)  # Reproduz o som no canal disponível
            else:
                print("Todos os canais estão ocupados. Não foi possível tocar o áudio.")
        else:
            print(f"Arquivo de áudio não encontrado: {audio_path}")
    except Exception as e:
        print(f"Erro ao tocar o áudio: {e}")


# Função para carregar as codificações faciais do arquivo pickle
def load_encodings(pickle_file):
    try:
        with open(pickle_file, 'rb') as f:
            data = pickle.load(f)  # Carrega o arquivo pickle
        return data['users']  # Retorna a lista de usuários
    except FileNotFoundError:
        print(f"Arquivo {pickle_file} não encontrado.")
        return []
    except Exception as e:
        print(f"Erro ao carregar o arquivo pickle: {e}")
        return []


# Função principal para reconhecimento facial
def recognize_faces_from_webcam(encodings_file, frame_skip=10, resize_scale=0.7):
    print("[INFO] Carregando codificações faciais...")
    users = load_encodings(encodings_file)  # Agora carregamos a lista de usuários

    if not users:
        print("Nenhum usuário encontrado no arquivo de codificações.")
        return

    played_audios = set()
    previous_frame_names = set()  # Reter os nomes das pessoas no frame anterior
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

        boxes = face_recognition.face_locations(rgb_frame, model="hog")
        encodings = face_recognition.face_encodings(rgb_frame, boxes)

        names = []
        for encoding in encodings:
            name = "Unknown"
            for user in users:
                matches = face_recognition.compare_faces(user['encodings'], encoding, tolerance=0.5)
                if True in matches:
                    name = user['name']
                    break

            names.append(name)

        current_frame_names = set(names)  # Reter os nomes das pessoas no frame atual

        for name in current_frame_names:
            if name != "Unknown" and name not in previous_frame_names:
                user = next(user for user in users if user['name'] == name)
                audio_path = os.path.join('/home/felipe/static/audio', user['audio'])
                print(f"Tocando áudio: {audio_path}")
                play_audio(audio_path)

                if user['item'] == '21':  # Suponha que a porta 21 está vinculada a este item
                    activate_gpio(user['item'])
                    print(f"Ativando GPIO 21 para {name}")

        previous_frame_names = current_frame_names

        for ((top, right, bottom, left), name) in zip(boxes, names):
            if name != "Unknown":
                print(f"Pessoa reconhecida: {name}")

            top = int(top / resize_scale)
            right = int(right / resize_scale)
            bottom = int(bottom / resize_scale)
            left = int(left / resize_scale)

            cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 2)
            y = top - 15 if top - 15 > 15 else top + 15
            cv2.putText(frame, name, (left, y), cv2.FONT_HERSHEY_SIMPLEX, 0.75, (0, 255, 0), 2)


    # Libera os recursos da câmera após sair do loop
    video_capture.release()


# Caminho para o arquivo pickle com as codificações faciais
encodings_file = '/home/felipe/encodings.pkl'

# Inicia o reconhecimento facial
recognize_faces_from_webcam(encodings_file, frame_skip=20, resize_scale=0.5)
