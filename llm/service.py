import requests
import os

class LLMService:
    def __init__(self, base_url=None):
        self.base_url = base_url or os.getenv("COE_BACKEND_URL", "http://localhost:8000")
        self.chat_completions_url = f"{self.base_url}/v1/chat/completions"

    def chat_completion(self, messages, model="gpt-4", stream=False):
        headers = {
            "Content-Type": "application/json",
            # "Authorization": f"Bearer {os.getenv("OPENAI_API_KEY")}" # CoE-Backend handles its own auth
        }
        payload = {
            "model": model,
            "messages": messages,
            "stream": stream
        }
        try:
            response = requests.post(self.chat_completions_url, headers=headers, json=payload, stream=stream)
            response.raise_for_status() # Raise an exception for HTTP errors

            if stream:
                return response.iter_content(chunk_size=None)
            else:
                return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error communicating with LLM backend: {e}")
            return None
