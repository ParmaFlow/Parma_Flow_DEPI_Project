# core/llm.py
from openai import OpenAI

class LLMModel:
    def __init__(self, api_key):
        self.client = OpenAI(
            base_url="https://api.groq.com/openai/v1",
            api_key=api_key
        )

    # core/llm.py

    def get_decision(self, system_prompt, user_data):
        response = self.client.chat.completions.create(
            model="llama-3.1-8b-instant", 
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": str(user_data)}
            ],
            response_format={ "type": "json_object" } 
        )
        return response.choices[0].message.content