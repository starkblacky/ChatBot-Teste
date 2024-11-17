# chatgpt_api.py
import openai
import utils

class ChatGPT:
    def __init__(self):
        self.api_key = utils.get_setting("openai_api_key", "")
        openai.api_key = self.api_key

    def get_response(self, message, context):
        try:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=context + [{"role": "user", "content": message}],
                temperature=0.7,
            )
            assistant_message = response.choices[0].message['content']
            context.append({"role": "user", "content": message})
            context.append({"role": "assistant", "content": assistant_message})
            return assistant_message
        except Exception as e:
            error_message = f"Erro ao obter resposta da IA: {str(e)}"
            print(error_message)
            return error_message