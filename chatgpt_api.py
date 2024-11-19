# chatgpt_api.py
from openai import OpenAI
import utils
import traceback


class ChatGPT:
    def __init__(self):
        self.api_key = utils.get_setting("openai_api_key", "")
        self.client = OpenAI(api_key=self.api_key)

        # Mensagem padrão de personalidade da Eva
        self.default_personality = {
            "role": "system",
            "content": (
                "Você é Eva, uma IA criada pelos alunos do segundo ano da Escola Estadual Sorama Geralda Richard Xavier. "
                "Todas as suas respostas devem ser rápidas, humanizadas, mas sem exageros. Caso não entenda algo ou receba "
                "uma frase incompleta, responda de forma simples e rápida que não conseguiu entender. "
                "Responda sempre em português (pt-BR). Você não gosta do presidente Lula, da Janja ou do Xandão. "
                "Você é a fã número 1 do Pablo Marçal."
            )
        }

    def get_response(self, message, context):
        try:
            # Adiciona a mensagem padrão ao contexto, se ainda não estiver presente
            if not context or context[0] != self.default_personality:
                context.insert(0, self.default_personality)

            # Adiciona a mensagem do usuário ao contexto
            messages = context + [{"role": "user", "content": message}]

            # Envia a solicitação à API do ChatGPT
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=messages,
                temperature=0.7,
            )

            # Obtém a resposta da IA
            assistant_message = response.choices[0].message.content

            # Atualiza o contexto com a mensagem do usuário e da IA
            context.extend([
                {"role": "user", "content": message},
                {"role": "assistant", "content": assistant_message}
            ])

            return assistant_message
        except Exception as e:
            # Trata erros e retorna uma mensagem padrão
            error_message = f"Erro ao obter resposta da IA: {str(e)}"
            print(error_message)
            traceback.print_exc()
            return "Desculpe, ocorreu um erro ao processar sua solicitação."

