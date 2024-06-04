import os
import time
import openai
from dotenv import load_dotenv
from abc import ABC

class OpenAIEngine(ABC):
    def __init__(self, endpoint):
        load_dotenv()
        openai.api_key = 'ollama'
        openai.api_base = endpoint

    # Load environment variables from .env file
    def get_LLM_response(self, **kwargs):
        for _ in range(5):
            try:
                response = openai.ChatCompletion.create(**kwargs)
                return response  # If the above succeeds, we return here
            except Exception as e:
                save_err = e
                if isinstance(e, openai.error.ServiceUnavailableError):
                    time.sleep(1)
                elif "The server had an error processing your request." in str(e):
                    time.sleep(1)
                else:
                    break
        raise save_err