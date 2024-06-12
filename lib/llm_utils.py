import os
import time
import openai
from dotenv import load_dotenv
from abc import ABC
import json

class OpenAIEngine(ABC):
    def __init__(self, endpoint):
        load_dotenv()
        openai.api_key = 'ollama'
        openai.api_base = endpoint

    def _funcCall2str(self, function_call):
        return function_call['name']+'('+', '.join(f'{k}={v}' for k, v in json.loads(function_call['arguments']).items())+')'

    def _messages2prompt(self, messages):
        full_str = ''
        for m in messages:
            role_str = m['role'].title()+': '
            content_str = m['content'] if m['content'] is not None else ''
            func_call_str = 'Function call: ' + self._funcCall2str(m['function_call']) if 'function_call' in m else ''
            full_str += role_str + content_str + func_call_str + '\n'
        full_str += 'Assistant:'
        return full_str

    def parse_response(self, response):
        if 'Function call:' in response:
            response = [line for line in response.splitlines() if 'Function call:' in line][0]
            print(f'Asking result for {response}')
            true_response = response.replace('Function call:', '').strip()
            func_name = true_response.split('(')[0]
                
            arg_value = true_response.split('(')[1].removesuffix(')')
            if '=' in arg_value:
                arg_value = arg_value.split('=')[-1]
            arg_value = arg_value.strip('"').strip("'")
            if func_name == 'get_failing_tests_covered_methods_for_class':
                args_dict = {'class_name': arg_value}
            elif func_name == 'get_failing_tests_covered_classes': 
                args_dict = {}
            else:
                args_dict = {'signature': arg_value}
            response_obj = {'choices': [{"message": {
                'role': "assistant",
                "content": None,
                "function_call": {
                    "name": func_name,
                    "arguments": json.dumps(args_dict),
                }
            }}]}
            return response_obj
        else:
            response_obj = {'choices': [{"message": {
                'role': "assistant",
                "content": response,
            }}]}
            return response_obj

    # Load environment variables from .env file
    def get_LLM_response(self, **kwargs):
        for _ in range(5):
            try:
                kwargs['messages'] = [{'role': 'system', 'content': self._messages2prompt(kwargs['messages'])}]
                response = openai.ChatCompletion.create(**kwargs)
                return self.parse_response(response['choices'][0]['message']['content'])  # If the above succeeds, we return here
            except Exception as e:
                save_err = e
                if isinstance(e, openai.error.ServiceUnavailableError):
                    time.sleep(1)
                elif "The server had an error processing your request." in str(e):
                    time.sleep(1)
                else:
                    break
        raise save_err