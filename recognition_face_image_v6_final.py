# -----------------------------------------------------------#
# Projeto   : Sistema de reconhecimento facial Rasberry
# File Name : recogintion_face_imagem_v6_final.py
# Data      : 01/09/2024                                     #
# Autor(a)s : Walner de Oliveira /                           #
# Objetivo  : executar em Webcam o reconhecimento facial     #
# Alteracao : 09/09/2024                                    #
#                                                            #
# -----------------------------------------------------------#

#requeriments.txt


### audi com um mais de um canal - se tiver dois rostos o audio toca os dois.

import face_recognition  # Biblioteca de reconhecimento facial
import pickle  # Substitui json por pickle para carregar e salvar os encodings
import cv2  # Biblioteca para manipulação de imagens e vídeo
import pygame  # Biblioteca para tocar áudio
import os


# Inicializar o mixer do pygame e definir múltiplos canais
pygame.mixer.init()
pygame.mixer.set_num_channels(8)  # Permite até 8 canais de áudio simultâneos

# Função para tocar o áudio usando pygame em um canal específico
def play_audio(audio_path):
    """
    Toca o arquivo de áudio usando o pygame em um canal disponível.
    :param audio_path: Caminho para o arquivo de áudio.
    """
    try:
        channel = pygame.mixer.find_channel()  # Encontra um canal livre
        if channel is not None:
            sound = pygame.mixer.Sound(audio_path)  # Carrega o som
            channel.play(sound)  # Reproduz o som no canal disponível
        else:
            print("Todos os canais estão ocupados. Não foi possível tocar o áudio.")
    except Exception as e:
        print(f"Erro ao tocar o áudio: {e}")

# Função para carregar as codificações faciais do arquivo pickle
def load_encodings(pickle_file):
    """
    Carrega os dados de codificações faciais, nomes e arquivos de áudio do arquivo pickle.
    :param pickle_file: Caminho para o arquivo pickle que contém as codificações faciais.
    :return: Lista de dicionários de usuários contendo 'name', 'audio', e 'encodings'.
    """
    with open(pickle_file, 'rb') as f:
        data = pickle.load(f)  # Carrega o arquivo pickle
    return data['users']  # Retorna a lista de usuários

# Função principal para reconhecimento facial
def recognize_faces_from_webcam(encodings_file, frame_skip=10, resize_scale=0.7):  # Ajuste frame_skip e resize_scale
    """
    Realiza reconhecimento facial usando a webcam, tocando o áudio correspondente ao rosto reconhecido.
    """
    print("[INFO] Carregando codificações faciais...")
    users = load_encodings(encodings_file)  # Agora carregamos a lista de usuários

    played_audios = set()
    video_capture = cv2.VideoCapture(0)
    frame_count = 0

    while True:
        ret, frame = video_capture.read()

        if frame_count % frame_skip != 0:
            frame_count += 1
            continue

        frame_count += 1
        small_frame = cv2.resize(frame, (0, 0), fx=resize_scale, fy=resize_scale)
        rgb_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)

        boxes = face_recognition.face_locations(rgb_frame, model="hog")  # Teste com 'cnn' se necessário
        encodings = face_recognition.face_encodings(rgb_frame, boxes)

        names = []
        for encoding in encodings:
            name = "Unknown"
            for user in users:
                matches = face_recognition.compare_faces(user['encodings'], encoding, tolerance=0.5)  # Teste tolerâncias

                if True in matches:
                    name = user['name']
                    break  # Se encontrar a correspondência, não precisa continuar verificando outros usuários

            names.append(name)

        for ((top, right, bottom, left), name) in zip(boxes, names):
            top = int(top / resize_scale)
            right = int(right / resize_scale)
            bottom = int(bottom / resize_scale)
            left = int(left / resize_scale)

            cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 2)
            y = top - 15 if top - 15 > 15 else top + 15
            cv2.putText(frame, name, (left, y), cv2.FONT_HERSHEY_SIMPLEX, 0.75, (0, 255, 0), 2)

            if name != "Unknown" and name not in played_audios:
                # Busca o áudio associado ao nome
                user = next(user for user in users if user['name'] == name)
                audio_path = os.path.join('static/audio', user['audio'])
                print(f"Tocando áudio: {audio_path}")
                play_audio(audio_path)  # Toca o áudio usando canais diferentes
                played_audios.add(name)

        cv2.imshow("Webcam - Reconhecimento Facial", frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    video_capture.release()
    cv2.destroyAllWindows()


# Caminho para o arquivo pickle com as codificações faciais
encodings_file = 'encodings.pkl'  # Alterado para o arquivo pickle

# Inicia o reconhecimento facial, ignorando frames e ajustando a resolução
recognize_faces_from_webcam(encodings_file, frame_skip=5, resize_scale=0.5)


### audi com um canal

'''
import face_recognition  # Biblioteca de reconhecimento facial
import pickle  # Substitui json por pickle para carregar e salvar os encodings
import cv2  # Biblioteca para manipulação de imagens e vídeo
import pygame  # Biblioteca para tocar áudio
import os


# Inicializar o mixer do pygame
pygame.mixer.init()

# Função para tocar o áudio usando pygame
def play_audio(audio_path):
    """
    Toca o arquivo de áudio usando o pygame.
    :param audio_path: Caminho para o arquivo de áudio.
    """
    pygame.mixer.music.load(audio_path)
    pygame.mixer.music.play()

# Função para carregar as codificações faciais do arquivo pickle
def load_encodings(pickle_file):
    """
    Carrega os dados de codificações faciais, nomes e arquivos de áudio do arquivo pickle.
    :param pickle_file: Caminho para o arquivo pickle que contém as codificações faciais.
    :return: Lista de dicionários de usuários contendo 'name', 'audio', e 'encodings'.
    """
    with open(pickle_file, 'rb') as f:
        data = pickle.load(f)  # Carrega o arquivo pickle
    return data['users']  # Retorna a lista de usuários

# Função principal para reconhecimento facial
def recognize_faces_from_webcam(encodings_file, frame_skip=10, resize_scale=0.7):  # Ajuste frame_skip e resize_scale
    """
    Realiza reconhecimento facial usando a webcam, tocando o áudio correspondente ao rosto reconhecido.
    """
    print("[INFO] Carregando codificações faciais...")
    users = load_encodings(encodings_file)  # Agora carregamos a lista de usuários

    played_audios = set()
    video_capture = cv2.VideoCapture(0)
    frame_count = 0

    while True:
        ret, frame = video_capture.read()

        if frame_count % frame_skip != 0:
            frame_count += 1
            continue

        frame_count += 1
        small_frame = cv2.resize(frame, (0, 0), fx=resize_scale, fy=resize_scale)
        rgb_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)

        boxes = face_recognition.face_locations(rgb_frame, model="hog")  # Teste com 'cnn' se necessário
        encodings = face_recognition.face_encodings(rgb_frame, boxes)

        names = []
        for encoding in encodings:
            name = "Unknown"
            for user in users:
                matches = face_recognition.compare_faces(user['encodings'], encoding, tolerance=0.5)  # Teste tolerâncias

                if True in matches:
                    name = user['name']
                    break  # Se encontrar a correspondência, não precisa continuar verificando outros usuários

            names.append(name)

        for ((top, right, bottom, left), name) in zip(boxes, names):
            top = int(top / resize_scale)
            right = int(right / resize_scale)
            bottom = int(bottom / resize_scale)
            left = int(left / resize_scale)

            cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 2)
            y = top - 15 if top - 15 > 15 else top + 15
            cv2.putText(frame, name, (left, y), cv2.FONT_HERSHEY_SIMPLEX, 0.75, (0, 255, 0), 2)

            if name != "Unknown" and name not in played_audios:
                # Busca o áudio associado ao nome
                user = next(user for user in users if user['name'] == name)
                audio_path = os.path.join('static/audio', user['audio'])
                print(f"Tocando áudio: {audio_path}")
                play_audio(audio_path)
                played_audios.add(name)

        cv2.imshow("Webcam - Reconhecimento Facial", frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    video_capture.release()
    cv2.destroyAllWindows()


# Caminho para o arquivo pickle com as codificações faciais
encodings_file = 'encodings.pkl'  # Alterado para o arquivo pickle

# Inicia o reconhecimento facial, ignorando frames e ajustando a resolução
recognize_faces_from_webcam(encodings_file, frame_skip=5, resize_scale=0.5)
'''
