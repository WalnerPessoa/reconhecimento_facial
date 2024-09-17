import pickle  # Substitui json por pickle para carregar e salvar os encodings
import json  # Para converter em formato JSON


def load_encodings(pickle_file):
    """
    Carrega os dados de codificações faciais, nomes e arquivos de áudio do arquivo pickle e converte para JSON.
    :param pickle_file: Caminho para o arquivo pickle que contém as codificações faciais.
    :return: Dados carregados no formato JSON.
    """
    with open(pickle_file, 'rb') as f:
        data = pickle.load(f)  # Carrega o arquivo pickle

    # Converter para JSON
    data_json = json.dumps(data, indent=4)

    print(data_json)  # Exibe o JSON para depuração
    return data_json


load_encodings("encodings.pkl")

'''

import pickle  # Substitui json por pickle para carregar e salvar os encodings

def load_encodings(pickle_file):
    """
    Carrega os dados de codificações faciais, nomes e arquivos de áudio do arquivo pickle.
    :param pickle_file: Caminho para o arquivo pickle que contém as codificações faciais.
    :return: Dicionário contendo 'names', 'encodings', e 'audios'.
    """
    with open(pickle_file, 'rb') as f:
        data = pickle.load(f)  # Carrega o arquivo pickle
    print(data)  # Exibe o conteúdo do dicionário para depuração
    return data


load_encodings("encodings.pkl")

'''