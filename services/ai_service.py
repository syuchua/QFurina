from utils.client import OpenAIClient
from app.Core.config import Config

config = Config.get_instance()
client = OpenAIClient(config.API_KEY, config.API_BASE)

class AIService:
    @staticmethod
    async def get_chat_response(messages):
        return await client.chat_completion(config.MODEL, messages)

    @staticmethod
    async def generate_image(prompt):
        return await client.image_generation(config.IMAGE_MODEL, prompt)
