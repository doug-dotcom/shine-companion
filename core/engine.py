import os
from openai import OpenAI


class CoreEngine:
    def __init__(self):
        # Explicitly load API key from environment
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY not found in environment.")

        # Explicit client injection (critical for Railway)
        self.client = OpenAI(api_key=api_key)

        # Model (defaults safely to mini)
        self.model = os.getenv("SHINE_MODEL", "gpt-4o-mini")

    def generate_from_messages(self, messages):
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.7,
            )

            return response.choices[0].message.content

        except Exception as e:
            print("==== OPENAI ERROR ====")
            print(str(e))
            raise