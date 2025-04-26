import os
import requests
from dotenv import load_dotenv


API_KEY = "XF3ZGC6zQj2s0Aj7ugjbI7D87tzdsP1n"


class DeepInfraChat:
    def __init__(self):
        self.models = {
            'Mixtral 8x22B-Instruct': {
                "model": "mistralai/Mixtral-8x22B-Instruct-v0.1",
                "parameters": {"temperature": 0.7, "max_tokens": 500}
            },
            'Llama-3-70B-Instruct': {
                "model": "meta-llama/Meta-Llama-3-70B-Instruct",
                "parameters": {"temperature": 0.5, "max_tokens": 1000}
            }
        }
        self.base_url = "https://api.deepinfra.com/v1/openai/chat/completions"
        self.headers = {
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json"
        }

    def generate_response(self, model_name, prompt):
        """Генерирует ответ от выбранной модели"""
        if model_name not in self.models:
            raise ValueError(f"Модель {model_name} не найдена")

        model_config = self.models[model_name]
        payload = {
            "model": model_config["model"],
            "messages": [{"role": "user", "content": prompt}],
            **model_config["parameters"]
        }

        try:
            response = requests.post(
                self.base_url,
                json=payload,
                headers=self.headers,
                timeout=30
            )
            response.raise_for_status()
            return response.json()["choices"][0]["message"]["content"]
        except Exception as e:
            return f"Ошибка: {str(e)}"

    def chat_with_all_models(self, prompt: str) -> dict:
        results = {'choices': []}
        for model_name in self.models:
            response = self.generate_response(model_name, prompt)
            results['choices'].append({'text': response, 'model': model_name})
        return results

# chat = DeepInfraChat()
# responses = chat.chat_with_all_models(user_input)
# @app.route('/')
# def index():
#     return render_template('index.html')
#
#
# @app.route('/send-message', methods=['POST'])
# def send_message():
#     user_message = request.json.get('message')
#     return jsonify(chat.chat_with_all_models(user_message))
#
#
# if __name__ == '__main__':
#     app.run(debug=True)