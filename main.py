# -----------------------------------------------------------#
# Projeto   : Sistema de reconhecimento facial Rasberry      #
# File Name : recogintion_face_imagem_v6_final.py            #
# Data      : 16/09/2024                                     #
# Autor(a)s : Walner de Oliveira /                           #
# Objetivo  : executar em Webcam o reconhecimento facial     #
# Alteracao : 09/09/2024                                     #
#                                                            #
# arquivos desse sistema:                                    #
# rec_facial.py                                              #
# main.py                                                    #
# ativar_gpio.py                                             #
# -----------------------------------------------------------#
#USO

#uvicorn main:app --reload


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
            <style>
                body {
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    height: 100vh;
                    margin: 0;
                    font-family: Arial, sans-serif;
                    background-color: #f0f0f0;
                }
                .container {
                    text-align: center;
                    background-color: white;
                    padding: 20px;
                    border-radius: 10px;
                    box-shadow: 0px 0px 15px rgba(0, 0, 0, 0.1);
                }
                form {
                    margin-top: 20px;
                }
                input[type="text"], input[type="file"], select {
                    width: 100%;
                    padding: 10px;
                    margin: 10px 0;
                    border: 1px solid #ccc;
                    border-radius: 5px;
                }
                input[type="submit"] {
                    padding: 10px 20px;
                    background-color: #007bff;
                    color: white;
                    border: none;
                    border-radius: 5px;
                    cursor: pointer;
                }
                input[type="submit"]:hover {
                    background-color: #0056b3;
                }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>CADASTRE AQUI NOVO USUÁRIO</h1>
                <form action="/upload/" enctype="multipart/form-data" method="post">
                    <label for="name">Nome do Usuário:</label>
                    <input type="text" id="name" name="name" required><br><br>

                    <label for="photo">Anexar Fotos:</label>
                    <input type="file" id="photo" name="photos" accept="image/*" multiple required><br><br>

                    <label for="audio">Anexar Áudio:</label>
                    <input type="file" id="audio" name="audio" accept="audio/*" required><br><br>

                    <label for="item">Selecione um Item:</label>
                    <select id="item" name="item" required>
                        <option value="4">4</option>
                        <option value="5">5</option>
                        <option value="6">6</option>
                        <option value="12">12</option>
                        <option value="13">13</option>
                        <option value="16">16</option>
                        <option value="17">17</option>
                        <option value="18">18</option>
                        <option value="19">19</option>
                        <option value="20">20</option>
                        <option value="21">21</option>
                        <option value="22">22</option>
                        <option value="23">23</option>
                        <option value="24">24</option>
                        <option value="25">25</option>
                        <option value="26">26</option>
                        <option value="27">27</option>
                        <option value="36">36</option>
                        <option value="38">38</option>
                        <option value="40">40</option>
                    </select><br><br>

                    <input type="submit" value="Cadastrar Usuário">
                </form>
            </div>
        </body>
    </html>
    """

# Rota para lidar com o envio de imagens, áudio e item
@app.post("/upload/")
async def upload(
        name: str = Form(...),
        photos: List[UploadFile] = File(...),
        audio: UploadFile = File(...),
        item: str = Form(...)  # Novo campo adicionado para capturar o valor do item
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
            'encodings': user_encodings,
            'item': item  # Incluindo o item selecionado no cadastro
        })

    # Salva os dados atualizados no arquivo pickle
    with open(pickle_file, 'wb') as f:
        pickle.dump(data, f)

    # Redireciona de volta para a página inicial após o cadastro
    return RedirectResponse(url="/", status_code=303)


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
