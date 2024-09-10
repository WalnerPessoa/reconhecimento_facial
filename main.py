# -----------------------------------------------------------#
# Projeto   : Sistema de reconhecimento facial Rasberry      #
# File Name : main_v2.py                                     #
# Data      : 01/09/2024                                     #
# Autor(a)s : Walner de Oliveira /                           #
# Objetivo  : API para insumos do reconhecimento facial      #
# Alteracao : 09/09/2024                                     #
#                                                            #
# -----------------------------------------------------------#

#USO

#uvicorn main_v2:app --reload


import os
import pickle  # Usar pickle para serialização binária
import face_recognition
from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from typing import List
import uvicorn

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

    # Carrega o arquivo pickle existente ou cria um novo
    pickle_file = 'encodings.pkl'
    if os.path.exists(pickle_file):
        with open(pickle_file, 'rb') as f:
            data = pickle.load(f)
    else:
        data = {'users': []}  # Estrutura com uma lista de usuários

    # Verifica se o nome já existe no JSON
    user_exists = False
    for user in data['users']:
        if user['name'] == name:
            # Se o usuário já existe, adiciona as novas codificações à lista de encodings
            user['encodings'].extend(user_encodings)
            user_exists = True
            break

    if not user_exists:
        # Se o usuário não existe, cria um novo registro
        data['users'].append({
            'name': name,
            'audio': audio.filename,
            'encodings': user_encodings
        })

    # Salva os dados atualizados no arquivo pickle
    with open(pickle_file, 'wb') as f:
        pickle.dump(data, f)

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
