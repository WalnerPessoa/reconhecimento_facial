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