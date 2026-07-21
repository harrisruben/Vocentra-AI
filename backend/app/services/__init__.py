# Services package initialization
from app.services.base_provider import VoiceProvider
from app.services.vapi_provider import VapiProvider

_provider = VapiProvider()

def get_voice_provider() -> VoiceProvider:
    return _provider

class VapiService:
    @classmethod
    async def get_calls(cls):
        return await _provider.get_calls()

    @classmethod
    async def get_call(cls, call_id: str):
        return await _provider.get_call(call_id)

    @classmethod
    async def get_assistants(cls):
        return await _provider.get_assistants()

    @classmethod
    async def get_phone_numbers(cls):
        return await _provider.get_phone_numbers()

    @classmethod
    async def start_call(cls, assistant_id: str, phone_number_id, customer_number: str, metadata=None):
        return await _provider.start_call(assistant_id, phone_number_id, customer_number, metadata)

    @classmethod
    async def end_call(cls, call_id: str):
        return await _provider.end_call(call_id)

