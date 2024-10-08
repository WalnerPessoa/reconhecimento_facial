
# -----------------------------------------------------------#
# Projeto   : Sistema de reconhecimento facial Rasberry      #
# File Name : main_back2.py                                        #
# Data      : 01/09/2024                                     #
# Autor(a)s : Walner de Oliveira /                           #
# Objetivo  : API para insumos do reconhecimento facial      #
# Alteracao : XX/XX/XXXX                                     #
#                                                            #
# -----------------------------------------------------------#
#USO

#uvicorn main:app --reload

import os
import json
import face_recognition
from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from typing import List
import uvicorn
from threading import Thread

app = FastAPI()

# Monta o diretório estático para servir arquivos de áudio
app.mount("/static", StaticFiles(directory="static"), name="static")

# Pastas onde as imagens e áudios serão salvos
UPLOAD_FOLDER = 'dataset/'
AUDIO_FOLDER = 'static/audio/'

# Certifique-se de que os diretórios existem
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(AUDIO_FOLDER, exist_ok=True)

# Função para carregar e codificar várias imagens
def load_face_encodings(image_paths):
    encodings = []
    for image_path in image_paths:
        image = face_recognition.load_image_file(image_path)
        encoding = face_recognition.face_encodings(image)
        if encoding:  # Verifica se foi possível encontrar uma face na imagem
            encodings.append(encoding[0].tolist())  # Adiciona a codificação à lista
    return encodings

# Página inicial para upload (HTML simples)
@app.get("/", response_class=HTMLResponse)
async def main():
    return """
    <html>
        <head>
            <title>Cadastro de Usuário</title>
        </head>
        <body>
            <h1>CADASTRE AQUI NOVO USUÁRIO</h1>
            <form action="/upload/" enctype="multipart/form-data" method="post">
                <label for="name">Nome do Usuário:</label>
                <input type="text" id="name" name="name" required><br><br>

                <label for="photo">Anexar Fotos:</label>
                <input type="file" id="photo" name="photos" accept="image/*" multiple required><br><br>

                <label for="audio">Anexar Áudio:</label>
                <input type="file" id="audio" name="audio" accept="audio/*" required><br><br>

                <input type="submit" value="Cadastrar Usuário">
            </form>
            <form action="/shutdown" method="post">
                <button type="submit">Sair</button>
            </form>
        </body>
    </html>
    """

# Rota para lidar com o envio de imagens e áudio
@app.post("/upload/")
async def upload(
        name: str = Form(...),
        photos: List[UploadFile] = File(...),
        audio: UploadFile = File(...)
):
    # Lista para armazenar os caminhos das imagens
    image_paths = []

    # Salva todas as imagens no diretório
    for photo in photos:
        photo_path = os.path.join(UPLOAD_FOLDER, photo.filename)
        with open(photo_path, "wb") as buffer:
            buffer.write(await photo.read())
        image_paths.append(photo_path)

    # Salva o áudio no diretório
    audio_path = os.path.join(AUDIO_FOLDER, audio.filename)
    with open(audio_path, "wb") as buffer:
        buffer.write(await audio.read())

    # Carrega todas as imagens e gera as codificações faciais
    user_encodings = load_face_encodings(image_paths)

    # Se nenhuma codificação facial for encontrada, retorne uma mensagem de erro
    if not user_encodings:
        return HTMLResponse(content="""
        <html>
            <head>
                <title>Erro no Cadastro</title>
            </head>
            <body>
                <h1>Erro: Nenhuma codificação facial encontrada nas imagens enviadas.</h1>
                <a href="/">Tentar Novamente</a>
            </body>
        </html>
        """, status_code=400)

    # Carrega o arquivo JSON existente ou cria um novo
    json_file = 'encodings.json'
    if os.path.exists(json_file):
        with open(json_file, 'r') as f:
            data = json.load(f)
    else:
        data = {'names': [], 'audios': [], 'encodings': []}

    # Adiciona as novas codificações e associa o áudio apenas uma vez
    data['names'].extend([name] * len(user_encodings))
    data['encodings'].extend(user_encodings)

    # Verifica se o nome já tem um áudio associado, se não, adiciona o áudio
    if name not in data['names']:
        data['audios'].append(audio.filename)
    elif audio.filename not in data['audios']:  # Evita duplicação de áudio
        data['audios'].append(audio.filename)

    # Salva os dados atualizados no arquivo JSON
    with open(json_file, 'w') as f:
        json.dump(data, f)

    # Redireciona de volta para a página inicial após o cadastro
    return RedirectResponse(url="/", status_code=303)

# Função para fazer shutdown do servidor
@app.post("/shutdown")
async def shutdown():
    shutdown_server()

def shutdown_server():
    os._exit(0)  # Encerra o servidor de forma imediata

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)

