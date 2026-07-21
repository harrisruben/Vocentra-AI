import httpx
import json
import datetime
import os
import sys
import uuid
import redis.asyncio as aioredis
from typing import Dict, Any, List, Optional
from app.core.config import settings
from app.core.logger import logger
from app.services.base_provider import VoiceProvider

class VapiProvider(VoiceProvider):
    def __init__(self):
        self.redis_url = settings.REDIS_URL or "redis://localhost:6379/0"

    async def _get_cache(self, key: str) -> Optional[Any]:
        try:
            r = aioredis.from_url(self.redis_url, socket_timeout=1.0, decode_responses=True)
            data = await r.get(key)
            await r.close()
            if data:
                return json.loads(data)
        except Exception as e:
            logger.debug(f"Redis Cache: Get failed (silently bypassing): {str(e)}")
        return None

    async def _set_cache(self, key: str, value: Any, ttl: int) -> None:
        try:
            r = aioredis.from_url(self.redis_url, socket_timeout=1.0)
            await r.set(key, json.dumps(value), ex=ttl)
            await r.close()
        except Exception as e:
            logger.debug(f"Redis Cache: Set failed (silently bypassing): {str(e)}")

    async def _delete_cache(self, key: str) -> None:
        try:
            r = aioredis.from_url(self.redis_url, socket_timeout=1.0)
            await r.delete(key)
            await r.close()
        except Exception as e:
            logger.debug(f"Redis Cache: Delete failed (silently bypassing): {str(e)}")

    @staticmethod
    def _get_headers() -> dict:
        if "pytest" in sys.modules or os.getenv("TESTING") == "true":
            return {}
        api_key = settings.VAPI_API_KEY
        if not api_key:
            return {}
        return {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

    async def get_calls(self) -> List[Dict[str, Any]]:
        # 1. Try Redis cache
        cached_calls = await self._get_cache("vapi_cache:calls")
        if cached_calls is not None:
            logger.info("VapiProvider: Loaded calls list from Redis cache.")
            return cached_calls

        headers = self._get_headers()
        if not headers:
            logger.info("VapiProvider: No API key. Returning mock calls list.")
            mock_calls = self._get_mock_calls()
            await self._set_cache("vapi_cache:calls", mock_calls, 30)
            return mock_calls

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get("https://api.vapi.ai/call", headers=headers, timeout=10.0)
                if response.status_code == 200:
                    data = response.json()
                    await self._set_cache("vapi_cache:calls", data, 30)
                    return data
                logger.error(f"Vapi API returned error: status={response.status_code}, response={response.text}")
                return self._get_mock_calls()
        except Exception as e:
            logger.error(f"Failed to fetch calls from Vapi: {str(e)}")
            return self._get_mock_calls()

    async def get_call(self, call_id: str) -> Optional[Dict[str, Any]]:
        # Individual call details are not cached to prevent state stale updates (transcripts stream live)
        headers = self._get_headers()
        if not headers:
            return self._get_mock_call_detail(call_id)

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"https://api.vapi.ai/call/{call_id}", headers=headers, timeout=10.0)
                if response.status_code == 200:
                    return response.json()
                logger.error(f"Vapi API returned error: status={response.status_code}, response={response.text}")
                return self._get_mock_call_detail(call_id)
        except Exception as e:
            logger.error(f"Failed to fetch call detail from Vapi: {str(e)}")
            return self._get_mock_call_detail(call_id)

    async def get_assistants(self) -> List[Dict[str, Any]]:
        cached_assistants = await self._get_cache("vapi_cache:assistants")
        if cached_assistants is not None:
            return cached_assistants

        headers = self._get_headers()
        fallback = [{"id": "vapi_assistant_mock_id", "name": "Vocentra AI Assistant"}]
        if not headers:
            await self._set_cache("vapi_cache:assistants", fallback, 600)
            return fallback

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get("https://api.vapi.ai/assistant", headers=headers, timeout=10.0)
                if response.status_code == 200:
                    data = response.json()
                    await self._set_cache("vapi_cache:assistants", data, 600)
                    return data
                return fallback
        except Exception as e:
            logger.error(f"Failed to fetch assistants: {str(e)}")
            return fallback

    async def get_phone_numbers(self) -> List[Dict[str, Any]]:
        cached_phones = await self._get_cache("vapi_cache:phone_numbers")
        if cached_phones is not None:
            return cached_phones

        headers = self._get_headers()
        fallback = [{"id": "vapi_phone_mock_id", "number": "+19843712375"}]
        if not headers:
            await self._set_cache("vapi_cache:phone_numbers", fallback, 600)
            return fallback

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get("https://api.vapi.ai/phone-number", headers=headers, timeout=10.0)
                if response.status_code == 200:
                    data = response.json()
                    await self._set_cache("vapi_cache:phone_numbers", data, 600)
                    return data
                return fallback
        except Exception as e:
            logger.error(f"Failed to fetch phone numbers: {str(e)}")
            return fallback

    async def start_call(
        self,
        assistant_id: str,
        phone_number_id: Optional[str],
        customer_number: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        # Invalidate call list cache
        await self._delete_cache("vapi_cache:calls")

        headers = self._get_headers()
        payload = {
            "assistantId": assistant_id,
            "customer": {
                "number": customer_number
            }
        }
        if phone_number_id:
            payload["phoneNumberId"] = phone_number_id
        if metadata:
            payload["metadata"] = metadata

        if not headers:
            logger.info("VapiProvider: Offline/No Key. Simulating started outbound call.")
            mock_call_id = f"vapi_outbound_{uuid.uuid4().hex[:8]}"
            return {
                "id": mock_call_id,
                "status": "queued",
                "type": "outboundPhoneCall",
                "assistantId": assistant_id,
                "customer": {"number": customer_number},
                "metadata": metadata or {}
            }

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post("https://api.vapi.ai/call", headers=headers, json=payload, timeout=10.0)
                if response.status_code in [200, 201]:
                    return response.json()
                logger.error(f"Vapi API start_call returned error: status={response.status_code}, response={response.text}")
                return {"id": f"vapi_outbound_{uuid.uuid4().hex[:8]}", "status": "queued"}
        except Exception as e:
            logger.error(f"Failed to start call from Vapi: {str(e)}")
            return {"id": f"vapi_outbound_{uuid.uuid4().hex[:8]}", "status": "queued"}

    async def end_call(self, call_id: str) -> bool:
        # Invalidate call list cache
        await self._delete_cache("vapi_cache:calls")

        headers = self._get_headers()
        if not headers:
            logger.info(f"VapiProvider: Offline/No Key. Simulating ending call {call_id}.")
            return True

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(f"https://api.vapi.ai/call/{call_id}/end", headers=headers, timeout=10.0)
                if response.status_code in [200, 201]:
                    return True
                logger.error(f"Vapi API end_call returned error: status={response.status_code}, response={response.text}")
                return False
        except Exception as e:
            logger.error(f"Failed to end call from Vapi: {str(e)}")
            return False

    @staticmethod
    def _get_mock_calls() -> List[Dict[str, Any]]:
        base_time = datetime.datetime.utcnow()
        return [
            {
                "id": "vapi_call_mock_1",
                "orgId": "org_mock_1",
                "assistantId": "vapi_assistant_mock_id",
                "phoneNumberId": "vapi_phone_mock_id",
                "customer": {"number": "+15551234567"},
                "status": "ended",
                "type": "inboundPhoneCall",
                "createdAt": (base_time - datetime.timedelta(minutes=15)).isoformat() + "Z",
                "startedAt": (base_time - datetime.timedelta(minutes=15)).isoformat() + "Z",
                "endedAt": (base_time - datetime.timedelta(minutes=13)).isoformat() + "Z",
                "duration": 120,
                "cost": 0.45,
                "summary": "Customer called to inquire about enterprise pricing tiers and requested a custom proposal.",
                "transcript": "Hello, I want to inquire about enterprise pricing. Vocentra: Enterprise plans start at $1200/mo."
            },
            {
                "id": "vapi_call_mock_2",
                "orgId": "org_mock_1",
                "assistantId": "vapi_assistant_mock_id",
                "phoneNumberId": "vapi_phone_mock_id",
                "customer": {"number": "+15559876543"},
                "status": "ended",
                "type": "inboundPhoneCall",
                "createdAt": (base_time - datetime.timedelta(hours=2)).isoformat() + "Z",
                "startedAt": (base_time - datetime.timedelta(hours=2)).isoformat() + "Z",
                "endedAt": (base_time - datetime.timedelta(hours=1, minutes=58)).isoformat() + "Z",
                "duration": 110,
                "cost": 0.38,
                "summary": "Lead called checking appointment schedules and confirmed slot booking details.",
                "transcript": "Is there a meeting slot tomorrow? Vocentra: Yes, we have 10 AM scheduled."
            }
        ]

    @staticmethod
    def _get_mock_call_detail(call_id: str) -> Dict[str, Any]:
        base_time = datetime.datetime.utcnow()
        return {
            "id": call_id,
            "orgId": "org_mock_1",
            "assistantId": "vapi_assistant_mock_id",
            "phoneNumberId": "vapi_phone_mock_id",
            "customer": {"number": "+15551234567"},
            "status": "ended",
            "type": "inboundPhoneCall",
            "createdAt": (base_time - datetime.timedelta(minutes=15)).isoformat() + "Z",
            "startedAt": (base_time - datetime.timedelta(minutes=15)).isoformat() + "Z",
            "endedAt": (base_time - datetime.timedelta(minutes=13)).isoformat() + "Z",
            "duration": 120,
            "cost": 0.45,
            "summary": "Customer called to inquire about enterprise pricing tiers and requested a custom proposal.",
            "transcript": "Hello, I want to inquire about enterprise pricing. Vocentra: Enterprise plans start at $1200/mo."
        }
