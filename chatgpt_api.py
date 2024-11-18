# chatgpt_api.py
from openai import OpenAI
import utils
import traceback

class ChatGPT:
    def __init__(self):
        self.api_key = utils.get_setting("openai_api_key", "")
        self.client = OpenAI(api_key=self.api_key)

    def get_response(self, message, context):
        try:
            # Certifique-se de que o contexto está no formato correto
            messages = context + [{"role": "user", "content": message}]
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=messages,
                temperature=0.7,
            )
            assistant_message = response.choices[0].message.content
            context.extend([
                {"role": "user", "content": message},
                {"role": "assistant", "content": assistant_message}
            ])
            return assistant_message
        except Exception as e:
            error_message = f"Erro ao obter resposta da IA: {str(e)}"
            print(error_message)
            traceback.print_exc()
            return "Desculpe, ocorreu um erro ao processar sua solicitação."