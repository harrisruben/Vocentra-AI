import pytest
from app.services.vapi_service import VapiService

@pytest.mark.asyncio
async def test_vapi_service_proxy_fallback() -> None:
    # Verify mock fallback behavior when VAPI_API_KEY is not configured
    calls = await VapiService.get_calls()
    assert len(calls) > 0
    assert calls[0]["id"] == "vapi_call_mock_1"
    assert calls[0]["cost"] == 0.22

    detail = await VapiService.get_call("vapi_call_mock_1")
    assert detail is not None
    assert detail["id"] == "vapi_call_mock_1"
    assert len(detail["messages"]) > 0

    assistants = await VapiService.get_assistants()
    assert len(assistants) > 0
    assert assistants[0]["id"] == "vapi_assistant_mock_id"

    phones = await VapiService.get_phone_numbers()
    assert len(phones) > 0
    assert phones[0]["id"] == "vapi_phone_mock_id"

from app.services import get_voice_provider, VoiceProvider

@pytest.mark.asyncio
async def test_voice_provider_registry() -> None:
    provider = get_voice_provider()
    assert isinstance(provider, VoiceProvider)
    
    calls = await provider.get_calls()
    assert len(calls) > 0
    assert calls[0]["id"] == "vapi_call_mock_1"

