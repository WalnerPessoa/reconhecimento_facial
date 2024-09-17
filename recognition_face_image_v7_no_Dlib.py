import pickle
import cv2
import pygame
import os

# Inicializar o mixer do pygame e definir múltiplos canais
pygame.mixer.init()
pygame.mixer.set_num_channels(8)

# Função para tocar o áudio
def play_audio(audio_path):
    try:
        channel = pygame.mixer.find_channel()
        if channel is not None:
            sound = pygame.mixer.Sound(audio_path)
            channel.play(sound)
        else:
            print("Todos os canais estão ocupados.")
    except Exception as e:
        print(f"Erro ao tocar o áudio: {e}")

# Função para carregar as codificações faciais do arquivo pickle
def load_encodings(pickle_file):
    with open(pickle_file, 'rb') as f:
        data = pickle.load(f)
    return data['users']

# Função principal para reconhecimento facial
def recognize_faces_from_webcam(encodings_file, frame_skip=10, resize_scale=0.7):
    print("[INFO] Carregando codificações faciais...")
    users = load_encodings(encodings_file)

    played_audios = set()
    video_capture = cv2.VideoCapture(0)
    frame_count = 0
    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

    while True:
        ret, frame = video_capture.read()

        if frame_count % frame_skip != 0:
            frame_count += 1
            continue

        frame_count += 1
        small_frame = cv2.resize(frame, (0, 0), fx=resize_scale, fy=resize_scale)
        gray_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2GRAY)

        faces = face_cascade.detectMultiScale(gray_frame, 1.3, 5)

        names = []
        for (x, y, w, h) in faces:
            face = small_frame[y:y+h, x:x+w]
            encoding = cv2.resize(face, (128, 128)).flatten().tolist()

            name = "Unknown"
            for user in users:
                if any(cv2.norm(encoding, known_enc) < 300 for known_enc in user['encodings']):  # Ajustar tolerância
                    name = user['name']
                    break

            names.append(name)

        for (x, y, w, h), name in zip(faces, names):
            x = int(x / resize_scale)
            y = int(y / resize_scale)
            w = int(w / resize_scale)
            h = int(h / resize_scale)

            cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
            cv2.putText(frame, name, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.75, (0, 255, 0), 2)

            if name != "Unknown" and name not in played_audios:
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
encodings_file = 'encodings.pkl'

# Inicia o reconhecimento facial, ignorando frames e ajustando a resolução
recognize_faces_from_webcam(encodings_file, frame_skip=5, resize_scale=0.5)
