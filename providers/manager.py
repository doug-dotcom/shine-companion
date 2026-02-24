import os
from providers.openai_provider import OpenAIProvider

def get_provider():
    provider_name = os.getenv("AI_PROVIDER", "openai").lower()

    if provider_name == "openai":
        return OpenAIProvider()

    raise Exception(f"Unknown provider: {provider_name}")
