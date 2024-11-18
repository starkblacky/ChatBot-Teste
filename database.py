# database.py
# Como o sistema não vai mais lembrar dos usuários, podemos simplificar o código do banco de dados
# para apenas salvar e recuperar conversas gerais, sem associação a usuários específicos.

from pymongo import MongoClient
from datetime import datetime

# Configurações do MongoDB
DATABASE_NAME = 'assistente_virtual'
CONVERSATION_COLLECTION = 'conversations'

client = MongoClient('mongodb://localhost:27017/')
db = client[DATABASE_NAME]
conversations_collection = db[CONVERSATION_COLLECTION]

def setup_database():
    # Criar índices para otimizar consultas
    conversations_collection.create_index('timestamp')

def save_conversation(user_message, assistant_response):
    conversations_collection.insert_one({
        'user_message': user_message,
        'assistant_response': assistant_response,
        'timestamp': datetime.now()
    })

def get_conversation_history():
    conversations = conversations_collection.find().sort('timestamp', 1)
    conversation_history = []
    for conv in conversations:
        conversation_history.append({'role': 'user', 'content': conv['user_message']})
        conversation_history.append({'role': 'assistant', 'content': conv['assistant_response']})
    return conversation_history