import os
import traceback
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()


class CoreEngine:
    def __init__(self):
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY not found.")

        # Let the SDK read the key from environment
        self.client = OpenAI()

        # Configurable model (change if needed)
        self.model = os.getenv("SHINE_MODEL", "gpt-4o-mini")

    def generate_from_messages(self, messages):
        try:
            resp = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
            )

            return resp.choices[0].message.content

        except Exception as e:
            print("===== OPENAI ERROR =====")
            traceback.print_exc()
            print("========================")
            raise