# -----------------------------------------------------------#
# Projeto   : Sistema de reconhecimento facial Rasberry      #
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

import face_recognition  # Biblioteca de reconhecimento facial
import json  # Para carregar e salvar os encodings em formato JSON
import cv2  # Biblioteca para manipulação de imagens e vídeo
from playsound import playsound  # Biblioteca para tocar áudio
import os


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
def recognize_faces_from_webcam(encodings_file, frame_skip=5, resize_scale=0.5):
    """
    Realiza reconhecimento facial usando a webcam, tocando o áudio correspondente ao rosto reconhecido.

    :param encodings_file: Caminho para o arquivo JSON com as codificações faciais.
    :param frame_skip: Número de frames a serem ignorados antes de processar um novo frame.
    :param resize_scale: Escala de redução da imagem para melhorar a performance.
    """
    # Carrega o arquivo JSON com as codificações faciais
    print("[INFO] Carregando codificações faciais...")
    data = load_encodings(encodings_file)

    # Lista para controlar quais áudios já foram tocados
    played_audios = set()

    # Inicializa a captura da webcam (0 é o ID da webcam)
    video_capture = cv2.VideoCapture(0)

    # Contador de frames
    frame_count = 0

    # Loop para capturar e processar frames da webcam
    while True:
        # Captura um frame da webcam
        ret, frame = video_capture.read()

        # Ignora frames de acordo com o valor de frame_skip
        if frame_count % frame_skip != 0:
            frame_count += 1
            continue

        # Incrementa o contador de frames
        frame_count += 1

        # Reduz a resolução da imagem para melhorar a performance
        small_frame = cv2.resize(frame, (0, 0), fx=resize_scale, fy=resize_scale)

        # Converte o frame de BGR (formato OpenCV) para RGB (formato face_recognition)
        rgb_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)

        # Detecta as localizações das faces no frame
        boxes = face_recognition.face_locations(rgb_frame, model="hog")  # Usando HOG para leveza
        encodings = face_recognition.face_encodings(rgb_frame, boxes)

        names = []  # Lista para armazenar os nomes das faces reconhecidas

        # Compara as faces detectadas com as codificações conhecidas
        for encoding in encodings:
            matches = face_recognition.compare_faces(data["encodings"], encoding, tolerance=0.4)
            name = "Unknown"  # Define o nome como 'Desconhecido' se não houver correspondência

            if True in matches:
                # Encontra o índice da correspondência mais próxima
                matchedIdxs = [i for (i, b) in enumerate(matches) if b]
                counts = {}

                # Conta o número de vezes que o nome aparece nas correspondências
                for i in matchedIdxs:
                    name = data["names"][i]
                    counts[name] = counts.get(name, 0) + 1

                # Define o nome com mais correspondências
                name = max(counts, key=counts.get)

            names.append(name)

        # Desenha retângulos ao redor das faces e escreve os nomes
        for ((top, right, bottom, left), name) in zip(boxes, names):
            # Ajusta as coordenadas para a resolução original
            top = int(top / resize_scale)
            right = int(right / resize_scale)
            bottom = int(bottom / resize_scale)
            left = int(left / resize_scale)

            # Desenha o retângulo ao redor da face
            cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 2)
            y = top - 15 if top - 15 > 15 else top + 15
            # Escreve o nome abaixo da face
            cv2.putText(frame, name, (left, y), cv2.FONT_HERSHEY_SIMPLEX, 0.75, (0, 255, 0), 2)

            # Se o nome for reconhecido e o áudio correspondente ainda não foi tocado
            if name != "Unknown" and name not in played_audios:
                idx = data["names"].index(name)
                audio_path = os.path.join('static/audio', data["audios"][idx])
                print(f"Tocando áudio: {audio_path}")
                playsound(audio_path)  # Toca o áudio correspondente
                played_audios.add(name)  # Marca o áudio como tocado

        # Mostra o frame com as faces reconhecidas
        cv2.imshow("Webcam - Reconhecimento Facial", frame)

        # Se a tecla 'q' for pressionada, sai do loop
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    # Libera a webcam e fecha as janelas
    video_capture.release()
    cv2.destroyAllWindows()


# Caminho para o arquivo JSON com as codificações faciais
encodings_file = 'encodings.json'

# Inicia o reconhecimento facial, ignorando frames e ajustando a resolução
recognize_faces_from_webcam(encodings_file, frame_skip=5, resize_scale=0.5)
