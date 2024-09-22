import pickle

# Caminho do arquivo encodings.pkl
encodings_file = '/home/felipe/encodings.pkl'
#encodings_file = 'encodings.pkl'

# Tente carregar o arquivo encodings.pkl e verificar o que ele contém
try:
    with open(encodings_file, 'rb') as f:
        data = pickle.load(f)

    # Exibir o conteúdo do arquivo
    print(f"Conteúdo de encodings.pkl: {data}")

    # Verifique se a chave 'users' está presente e exiba o número de usuários
    if 'users' in data:
        print(f"Total de usuários: {len(data['users'])}")
        for user in data['users']:
            print(f"Usuário: {user['name']}, Codificações: {len(user['encodings'])}")
    else:
        print("Chave 'users' não encontrada no arquivo encodings.pkl.")
except Exception as e:
    print(f"Erro ao carregar o arquivo encodings.pkl: {e}")
