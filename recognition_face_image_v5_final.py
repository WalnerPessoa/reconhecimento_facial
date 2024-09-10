# -----------------------------------------------------------#
# Projeto   : Sistema de reconhecimento facial Rasberry
# File Name : recogintion_face_imagem_v5_final.py
# Data      : 01/09/2024                                     #
# Autor(a)s : Walner de Oliveira /                           #
# Objetivo  : executar em Webcam o reconhecimento facial     #
# Alteracao : XX/XX/XXXX                                     #
#                                                            #
# -----------------------------------------------------------#

#gerar requeriments.txt
#pip install pipreqs
#pipreqs /Users/walnerpessoa/PycharmProjects/reconhecimento_facial_raspberry
#pip freeze | grep opencv-python >> requirements.txt
#pip freeze | grep python-multipart >> requirements.txt
#pip freeze | grep pygame >> requirements.txt



import face_recognition  # Biblioteca de reconhecimento facial
import json  # Para carregar e salvar os encodings em formato JSON
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

# Função para carregar as codificações faciais do arquivo JSON
def load_encodings(json_file):
    """
    Carrega os dados de codificações faciais, nomes e arquivos de áudio do arquivo JSON.

    :param json_file: Caminho para o arquivo JSON que contém as codificações faciais.
    :return: Dicionário contendo 'names', 'encodings', e 'audios'.
    """
    with open(json_file, 'r') as f:
        data = json.load(f)

    # Retorna as três chaves: names, encodings, e audios
    return {
        "names": data["names"],
        "encodings": [face_encoding for face_encoding in data["encodings"]],
        "audios": data["audios"]
    }


# Função principal para reconhecimento facial
def recognize_faces_from_webcam(encodings_file, frame_skip=10, resize_scale=0.7):  # Ajuste frame_skip e resize_scale
    """
    Realiza reconhecimento facial usando a webcam, tocando o áudio correspondente ao rosto reconhecido.
    """
    print("[INFO] Carregando codificações faciais...")
    data = load_encodings(encodings_file)

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
            matches = face_recognition.compare_faces(data["encodings"], encoding, tolerance=0.5)  # Teste tolerâncias
            name = "Unknown"

            if True in matches:
                matchedIdxs = [i for (i, b) in enumerate(matches) if b]
                counts = {}

                for i in matchedIdxs:
                    name = data["names"][i]
                    counts[name] = counts.get(name, 0) + 1

                name = max(counts, key=counts.get)

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
                idx = data["names"].index(name)
                audio_path = os.path.join('static/audio', data["audios"][idx])
                print(f"Tocando áudio: {audio_path}")
                play_audio(audio_path)
                played_audios.add(name)

        cv2.imshow("Webcam - Reconhecimento Facial", frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    video_capture.release()
    cv2.destroyAllWindows()



# Caminho para o arquivo JSON com as codificações faciais
encodings_file = 'encodings.json'

# Inicia o reconhecimento facial, ignorando frames e ajustando a resolução
recognize_faces_from_webcam(encodings_file, frame_skip=5, resize_scale=0.5)
