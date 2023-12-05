import os
from flask import *

import face_recognition

from azure.storage.blob import BlobServiceClient, ContainerClient

# https://www.geeksforgeeks.org/how-to-upload-file-in-python-flask/

# Ao iniciar a api
# Setup Azure - OK

# A cada req
# Receber a imagem na requisição - OK
# Carregar imagens do blob storage - OK
# Para cada imagem do blob
    # Fazer download - OK
    # Comparar com a imagem da requisição - OK
        # Se igual
            # Responder 200 com o nome da imagem do blob - OK
        # Se não igual
            # Responder com 404 - OK

def get_azure_container_client():
    # Connection string disponível em: Conta de Armazenamento > Chaves de Acesso -> Cadeia de conexão
    connection_string = 'DefaultEndpointsProtocol=https;AccountName=blobtestethiago;AccountKey=0q4CDkeOw7z33mt8OrSZSISmjCdjDnRBKxVrEpj2gv7ut/+ph2NrSGrtdhkmgtETLxh0TLXz8Pwh+AStqfVwnA==;EndpointSuffix=core.windows.net'
    nome_container = "imagens"

    blob_service_client = BlobServiceClient.from_connection_string(connection_string)
    container_client = blob_service_client.get_container_client(nome_container)

    return container_client


def carregar_lista_imagens(container_client: ContainerClient):
    lista_blobs = container_client.list_blobs()

    return lista_blobs

container_imagens = get_azure_container_client()  


app = Flask(__name__)

@app.route("/", methods=["GET"])
def hello_world():
    return "Hello World!"

@app.route("/login", methods=["POST"])
def login_post():
    # Salva imagem vinda da requisição
    file = request.files['imagem']
    file.save("./temp/" + file.filename)

    # Criar encoding com a imagem da requisição
    imagem_requisicao = face_recognition.load_image_file("./temp/" + file.filename)
    encoding_imagem_requisicao = face_recognition.face_encodings(imagem_requisicao)[0]

    # Carregar imagens do blob storage
    lista_blobs = carregar_lista_imagens(container_imagens)

    # Para cada imagem do blob
    for blob in lista_blobs:
        # Define o caminho e o nome do arquivo local
        file_path = os.path.join("./temp/", blob.name)

        # Faz download do blob para o arquivo local
        blob_imagem = container_imagens.get_blob_client(blob)
        imagem_baixada = blob_imagem.download_blob().content_as_bytes()

        with open(file_path, "wb") as f:
            f.write(imagem_baixada)

        # Criar encodings para a imagem do blob
        imagem_blob_carregada = face_recognition.load_image_file("./temp/" + blob.name)
        encoding_imagem_blob = face_recognition.face_encodings(imagem_blob_carregada)[0]

        # Comparar encoding da camera com o encoding blob
        resultado_comparacao = face_recognition.compare_faces([encoding_imagem_blob], encoding_imagem_requisicao)

        # Se match -> retornar 200 e nome da imagem
        if resultado_comparacao[0]:
            # Rosto corresponde à base
            body = "{ 'nomeImagem': '%s' }"%file.filename

            # Deletar imagem da requisição
            os.remove("./temp/" + file.filename)

            # Deletar imagem do blob
            os.remove("./temp/" + blob.name)

            return Response(body, status=200, mimetype="application/json")
        
        else:
            # Rosto não corresponde
            # Deletar imagem do blob
            os.remove("./temp/" + blob.name)

    # print(body)

    return Response("Usuario não encontrado", status=404)
