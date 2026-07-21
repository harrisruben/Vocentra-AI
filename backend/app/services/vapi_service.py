import httpx
import json
import redis.asyncio as aioredis
from typing import Dict, Any, List, Optional
from app.core.config import settings
from app.core.logger import logger
import datetime
import os
import sys
from urllib.parse import urlparse

class VapiService:
    CACHE_TTL_SECONDS = 300

    @staticmethod
    def _get_headers() -> dict:
        # Check if running under pytest to force mock data isolation
        if "pytest" in sys.modules or os.getenv("TESTING") == "true":
            return {}
        api_key = settings.VAPI_API_KEY
        if not api_key:
            return {}
        return {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

    @classmethod
    async def _get_cache(cls, key: str) -> Optional[Any]:
        try:
            redis_url = settings.REDIS_URL or "redis://localhost:6379/0"
            r = aioredis.from_url(redis_url, socket_timeout=1.0, decode_responses=True)
            data = await r.get(key)
            await r.close()
            if data:
                return json.loads(data)
        except Exception as e:
            logger.debug(f"VapiService cache get failed: {str(e)}")
        return None

    @classmethod
    async def _set_cache(cls, key: str, value: Any, ttl: int = CACHE_TTL_SECONDS) -> None:
        try:
            redis_url = settings.REDIS_URL or "redis://localhost:6379/0"
            r = aioredis.from_url(redis_url, socket_timeout=1.0)
            await r.set(key, json.dumps(value), ex=ttl)
            await r.close()
        except Exception as e:
            logger.debug(f"VapiService cache set failed: {str(e)}")

    @staticmethod
    def _coerce_datetime(value: Optional[Any]) -> Optional[str]:
        if not value:
            return None
        if isinstance(value, datetime.datetime):
            return value.isoformat()
        if isinstance(value, str):
            return value
        return str(value)

    @classmethod
    def _extract_recording_url(cls, payload: Any) -> Optional[str]:
        if not isinstance(payload, (dict, list)):
            return None

        candidates: List[tuple[int, str]] = []
        seen = set()

        def walk(value: Any, path: str = "") -> None:
            if isinstance(value, dict):
                for key, item in value.items():
                    normalized_key = str(key).lower()
                    if normalized_key in {"stereorecordingurl", "stereorecording_url", "stereo_recordingurl", "stereo_recording_url"}:
                        if isinstance(item, str) and item.strip() and item not in seen:
                            candidates.append((10, item))
                            seen.add(item)
                    elif normalized_key in {"recordingurl", "recording_url", "recording"}:
                        if isinstance(item, str) and item.strip() and item not in seen:
                            candidates.append((8, item))
                            seen.add(item)
                    elif normalized_key in {"url", "uri", "src", "href", "downloadurl", "download_url", "mediaurl", "media_url", "fileurl", "file_url"}:
                        if isinstance(item, str) and item.strip() and ("record" in path.lower() or "artifact" in path.lower() or "media" in path.lower() or "file" in path.lower()) and item not in seen:
                            candidates.append((4, item))
                            seen.add(item)
                    if normalized_key in {"artifacts", "media", "files", "recordings", "attachments", "recording"}:
                        walk(item, f"{path}.{key}")
                    elif isinstance(item, (dict, list)):
                        walk(item, f"{path}.{key}")
            elif isinstance(value, list):
                for idx, item in enumerate(value):
                    walk(item, f"{path}[{idx}]")

        walk(payload)
        if not candidates:
            return None
        candidates.sort(key=lambda item: item[0], reverse=True)
        return candidates[0][1]

    @classmethod
    def _extract_expiration(cls, payload: Any) -> Optional[str]:
        if not isinstance(payload, dict):
            return None

        for key in ("expiresAt", "expires_at", "recordingExpiresAt", "recording_expires_at"):
            value = payload.get(key)
            if value:
                return str(value)

        metadata = payload.get("metadata") or {}
        if isinstance(metadata, dict):
            for key in ("expiresAt", "expires_at", "recordingExpiresAt", "recording_expires_at"):
                value = metadata.get(key)
                if value:
                    return str(value)
        return None

    @classmethod
    def _extract_recording_metadata(cls, payload: Any) -> Dict[str, Any]:
        metadata = {}
        if isinstance(payload, dict):
            metadata.update({
                "size": payload.get("recordingSize") or payload.get("recording_size") or payload.get("size"),
                "mimeType": payload.get("mimeType") or payload.get("mime_type") or payload.get("audioMimeType") or payload.get("audio_mime_type"),
            })
            nested = payload.get("recording")
            if isinstance(nested, dict):
                metadata.update({
                    "size": metadata.get("size") or nested.get("size"),
                    "mimeType": metadata.get("mimeType") or nested.get("mimeType") or nested.get("mime_type"),
                })
        return metadata

    @classmethod
    def _log_recording_diagnostics(cls, call_id: Optional[str], payload: Any, recording_url: Optional[str], response_status: Optional[int] = None, error: Optional[str] = None) -> None:
        if not call_id:
            call_id = "unknown"
        parsed = urlparse(recording_url or "")
        metadata = cls._extract_recording_metadata(payload) if isinstance(payload, dict) else {}
        logger.info(
            "Vapi recording diagnostics | call_id=%s | recording_found=%s | recording_url_length=%s | recording_url_host=%s | expires_at=%s | recording_size=%s | audio_mime_type=%s | response_status=%s | error=%s",
            call_id,
            bool(recording_url),
            len(recording_url or ""),
            parsed.netloc or "None",
            cls._extract_expiration(payload) if isinstance(payload, dict) else None,
            metadata.get("size") or "None",
            metadata.get("mimeType") or "None",
            response_status or "None",
            error or "None",
        )

    @classmethod
    def _normalize_messages(cls, messages: Any) -> List[Dict[str, Any]]:
        if not messages:
            return []

        if isinstance(messages, str):
            transcript_lines = [line for line in messages.splitlines() if line.strip()]
            normalized: List[Dict[str, Any]] = []
            for idx, line in enumerate(transcript_lines):
                if ":" in line:
                    speaker, content = line.split(":", 1)
                    role = "assistant" if "vocentra" in speaker.lower() or "bot" in speaker.lower() or "assistant" in speaker.lower() else "user"
                    normalized.append({
                        "id": idx + 1,
                        "role": role,
                        "speaker": speaker.strip(),
                        "content": content.strip(),
                        "timestamp": None,
                        "type": "message"
                    })
                else:
                    normalized.append({
                        "id": idx + 1,
                        "role": "assistant",
                        "speaker": "Assistant",
                        "content": line.strip(),
                        "timestamp": None,
                        "type": "message"
                    })
            return normalized

        if isinstance(messages, list):
            normalized = []
            for idx, msg in enumerate(messages):
                if not isinstance(msg, dict):
                    continue
                role = msg.get("role") or msg.get("speaker") or msg.get("type") or "assistant"
                content = msg.get("message") or msg.get("content") or msg.get("text") or ""
                if not content:
                    continue
                normalized.append({
                    "id": idx + 1,
                    "role": "user" if str(role).lower() in {"user", "customer"} else "assistant",
                    "speaker": msg.get("speaker") or ("Customer" if str(role).lower() in {"user", "customer"} else "Assistant"),
                    "content": content,
                    "timestamp": msg.get("timestamp") or msg.get("time") or None,
                    "type": msg.get("type") or "message"
                })
            return normalized

        return []

    @classmethod
    def _normalize_call(cls, call: Dict[str, Any]) -> Dict[str, Any]:
        if not isinstance(call, dict):
            return {}

        assistant = call.get("assistant") or {}
        if isinstance(assistant, str):
            assistant = {"id": assistant, "name": assistant}
        elif not isinstance(assistant, dict):
            assistant = {}

        customer = call.get("customer") or {}
        if isinstance(customer, str):
            customer = {"number": customer}
        elif not isinstance(customer, dict):
            customer = {}

        analysis = call.get("analysis") or call.get("analytics") or {}
        if not isinstance(analysis, dict):
            analysis = {}

        latency_metrics = call.get("latencyMetrics") or call.get("latency") or {}
        if not isinstance(latency_metrics, dict):
            latency_metrics = {}

        tool_calls = call.get("toolCalls") or call.get("tool_calls") or []
        if not isinstance(tool_calls, list):
            tool_calls = []

        artifacts = call.get("artifacts") or []
        if not isinstance(artifacts, list):
            artifacts = []

        metadata = call.get("metadata") or {}
        if not isinstance(metadata, dict):
            metadata = {}

        transcript_value = call.get("transcript")
        transcript_messages = cls._normalize_messages(call.get("messages") or call.get("transcriptMessages") or transcript_value)
        transcript_text = transcript_value if isinstance(transcript_value, str) else None
        if not transcript_text and transcript_messages:
            transcript_text = "\n".join([msg.get("content", "") for msg in transcript_messages if msg.get("content")])

        recording_url = cls._extract_recording_url(call)
        stereo_recording_url = cls._extract_recording_url({
            "payload": call,
            "stereo": call.get("stereoRecordingUrl") or call.get("stereo_recording_url")
        })
        if stereo_recording_url and stereo_recording_url.startswith("http"):
            recording_url = stereo_recording_url
        if not recording_url:
            recording_url = call.get("recordingUrl") or call.get("recording_url")

        return {
            "id": call.get("id"),
            "callId": call.get("id"),
            "vapi_call_id": call.get("id"),
            "status": call.get("status", "ended"),
            "assistant": assistant,
            "assistantId": assistant.get("id") or call.get("assistantId"),
            "phoneNumberId": call.get("phoneNumberId"),
            "customer": customer,
            "duration": call.get("duration", 0),
            "endedReason": call.get("endedReason") or call.get("ended_reason"),
            "startedAt": cls._coerce_datetime(call.get("startedAt") or call.get("started_at")),
            "endedAt": cls._coerce_datetime(call.get("endedAt") or call.get("ended_at")),
            "createdAt": cls._coerce_datetime(call.get("createdAt") or call.get("created_at")),
            "cost": call.get("cost", 0.0),
            "recordingUrl": recording_url,
            "stereoRecordingUrl": stereo_recording_url or call.get("stereoRecordingUrl") or call.get("stereo_recording_url"),
            "summary": call.get("summary"),
            "transcript": transcript_messages,
            "transcriptText": transcript_text,
            "messages": transcript_messages,
            "analysis": analysis,
            "artifacts": artifacts,
            "provider": call.get("provider") or call.get("providerName"),
            "model": call.get("model") or call.get("modelName"),
            "voice": call.get("voice"),
            "latencyMetrics": latency_metrics,
            "toolCalls": tool_calls,
            "metadata": metadata,
            "type": call.get("type", "outboundPhoneCall"),
            "orgId": call.get("orgId")
        }

    @classmethod
    async def get_calls(cls) -> List[Dict[str, Any]]:
        cached_calls = await cls._get_cache("vapi_cache:calls")
        if cached_calls is not None:
            logger.info("VapiService: Loaded calls list from Redis cache.")
            return cached_calls

        headers = cls._get_headers()
        if not headers:
            logger.info("VapiService: No Vapi API key configured. Returning mock call logs.")
            mock_calls = [cls._normalize_call(call) for call in cls._get_mock_calls()]
            await cls._set_cache("vapi_cache:calls", mock_calls)
            return mock_calls

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get("https://api.vapi.ai/call", headers=headers, timeout=10.0)
                if response.status_code == 200:
                    payload = response.json()
                    if isinstance(payload, dict):
                        items = payload.get("data") or payload.get("calls") or []
                    else:
                        items = payload
                    normalized_calls = [cls._normalize_call(call) for call in items if isinstance(call, dict)]
                    await cls._set_cache("vapi_cache:calls", normalized_calls)
                    return normalized_calls
                logger.error(f"Vapi API returned error: status={response.status_code}, response={response.text}")
                fallback = [cls._normalize_call(call) for call in cls._get_mock_calls()]
                await cls._set_cache("vapi_cache:calls", fallback)
                return fallback
        except Exception as e:
            logger.error(f"Failed to fetch calls from Vapi: {str(e)}")
            fallback = [cls._normalize_call(call) for call in cls._get_mock_calls()]
            await cls._set_cache("vapi_cache:calls", fallback)
            return fallback

    @classmethod
    async def get_call(cls, call_id: str) -> Optional[Dict[str, Any]]:
        if not call_id:
            return None

        cache_key = f"vapi_cache:call:{call_id}"
        cached_call = await cls._get_cache(cache_key)
        if cached_call is not None:
            logger.info(f"VapiService: Loaded call {call_id} from Redis cache.")
            return cached_call

        headers = cls._get_headers()
        if not headers:
            logger.info(f"VapiService: No Vapi API key configured. Returning mock details for call_id={call_id}.")
            mock_detail = cls._normalize_call(cls._get_mock_call_detail(call_id))
            await cls._set_cache(cache_key, mock_detail)
            return mock_detail

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"https://api.vapi.ai/call/{call_id}", headers=headers, timeout=10.0)
                if response.status_code == 200:
                    payload = response.json()
                    if isinstance(payload, dict) and "data" in payload:
                        payload = payload["data"]
                    logger.info(f"Vapi raw call detail response for {call_id}: {json.dumps(payload, default=str)}")
                    normalized_call = cls._normalize_call(payload if isinstance(payload, dict) else {})
                    cls._log_recording_diagnostics(call_id, normalized_call, normalized_call.get("recordingUrl"), response.status_code)
                    await cls._set_cache(cache_key, normalized_call)
                    return normalized_call
                logger.error(f"Vapi API returned error: status={response.status_code}, response={response.text}")
                cls._log_recording_diagnostics(call_id, {}, None, response.status_code, response.text)
                fallback = cls._normalize_call(cls._get_mock_call_detail(call_id))
                await cls._set_cache(cache_key, fallback)
                return fallback
        except Exception as e:
            logger.error(f"Failed to fetch call detail from Vapi: {str(e)}")
            cls._log_recording_diagnostics(call_id, {}, None, None, str(e))
            fallback = cls._normalize_call(cls._get_mock_call_detail(call_id))
            await cls._set_cache(cache_key, fallback)
            return fallback

    @classmethod
    async def get_assistants(cls) -> List[Dict[str, Any]]:
        headers = cls._get_headers()
        if not headers:
            return [{"id": "vapi_assistant_mock_id", "name": "Vocentra AI Assistant"}]

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get("https://api.vapi.ai/assistant", headers=headers, timeout=10.0)
                if response.status_code == 200:
                    return response.json()
                return [{"id": "vapi_assistant_mock_id", "name": "Vocentra AI Assistant"}]
        except Exception as e:
            logger.error(f"Failed to fetch assistants: {str(e)}")
            return [{"id": "vapi_assistant_mock_id", "name": "Vocentra AI Assistant"}]

    @classmethod
    async def get_phone_numbers(cls) -> List[Dict[str, Any]]:
        headers = cls._get_headers()
        if not headers:
            return [{"id": "vapi_phone_mock_id", "number": "+19843712375"}]

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get("https://api.vapi.ai/phone-number", headers=headers, timeout=10.0)
                if response.status_code == 200:
                    return response.json()
                return [{"id": "vapi_phone_mock_id", "number": "+19843712375"}]
        except Exception as e:
            logger.error(f"Failed to fetch phone numbers: {str(e)}")
            return [{"id": "vapi_phone_mock_id", "number": "+19843712375"}]

    @classmethod
    async def start_call(
        cls,
        assistant_id: str,
        phone_number_id: Optional[str],
        customer_number: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        headers = cls._get_headers()
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
            logger.info("VapiService: Offline/No Key. Simulating started outbound call.")
            import uuid
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
                import uuid
                return {"id": f"vapi_outbound_{uuid.uuid4().hex[:8]}", "status": "queued"}
        except Exception as e:
            logger.error(f"Failed to start call from Vapi: {str(e)}")
            import uuid
            return {"id": f"vapi_outbound_{uuid.uuid4().hex[:8]}", "status": "queued"}

    @classmethod
    async def end_call(cls, call_id: str) -> bool:
        headers = cls._get_headers()
        if not headers:
            logger.info(f"VapiService: Offline/No Key. Simulating ending call {call_id}.")
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
        # Structured to replicate Vapi HTTP call list response
        base_time = datetime.datetime.utcnow()
        return [
            {
                "id": "vapi_call_mock_1",
                "orgId": "org_mock_1",
                "assistantId": "vapi_assistant_mock_id",
                "phoneNumberId": "vapi_phone_mock_id",
                "customer": {"number": "+19843712375"},
                "status": "ended",
                "type": "inboundPhoneCall",
                "endedReason": "customer-ended-call",
                "createdAt": (base_time - datetime.timedelta(minutes=15)).isoformat() + "Z",
                "startedAt": (base_time - datetime.timedelta(minutes=15)).isoformat() + "Z",
                "endedAt": (base_time - datetime.timedelta(minutes=13)).isoformat() + "Z",
                "duration": 147,
                "cost": 0.22,
                "summary": "Customer called to inquire about enterprise pricing tiers and requested a custom proposal.",
                "transcript": "Hello, I want to inquire about enterprise pricing. Vocentra: Enterprise plans start at $1200/mo.",
                "recordingUrl": "https://actions.google.com/sounds/v1/ambiences/morning_birds.ogg",
                "analysis": {
                    "sentiment": "positive",
                    "leadScore": 85
                }
            },
            {
                "id": "vapi_call_mock_2",
                "orgId": "org_mock_1",
                "assistantId": "vapi_assistant_mock_id",
                "phoneNumberId": "vapi_phone_mock_id",
                "customer": {"number": "+919025110211"},
                "status": "ended",
                "type": "outboundPhoneCall",
                "endedReason": "assistant-ended-call",
                "createdAt": (base_time - datetime.timedelta(hours=3)).isoformat() + "Z",
                "startedAt": (base_time - datetime.timedelta(hours=3)).isoformat() + "Z",
                "endedAt": (base_time - datetime.timedelta(hours=2, minutes=58, seconds=38)).isoformat() + "Z",
                "duration": 82,
                "cost": 0.25,
                "summary": "Customer scheduled a demo call for tomorrow morning to see the core dashboard features.",
                "transcript": "Hi, I'd like to book a product demo. Vocentra: Tomorrow morning works! Slot booked.",
                "recordingUrl": "https://actions.google.com/sounds/v1/ambiences/morning_birds.ogg",
                "analysis": {
                    "sentiment": "neutral",
                    "leadScore": 60
                }
            }
        ]

    @classmethod
    def _get_mock_call_detail(cls, call_id: str) -> Dict[str, Any]:
        calls = cls._get_mock_calls()
        for call in calls:
            if call["id"] == call_id:
                # Add full message timelines for detail preview
                call["messages"] = [
                    {"role": "user", "message": "Hello, I want to inquire about enterprise pricing.", "time": 1000},
                    {"role": "bot", "message": "Of course! Our Enterprise plans start at $1200/mo and offer custom integrations.", "time": 3000}
                ]
                return call
                
        # Return default if not in list
        return {
            "id": call_id,
            "orgId": "org_mock_1",
            "assistantId": "vapi_assistant_mock_id",
            "phoneNumberId": "vapi_phone_mock_id",
            "customer": {"number": "+15550199000"},
            "status": "ended",
            "type": "inboundPhoneCall",
            "createdAt": datetime.datetime.utcnow().isoformat() + "Z",
            "startedAt": datetime.datetime.utcnow().isoformat() + "Z",
            "endedAt": datetime.datetime.utcnow().isoformat() + "Z",
            "duration": 45,
            "cost": 0.35,
            "summary": "Customer requested scheduling info and scheduled a slot.",
            "transcript": "Hello, I'd like to schedule a product consulting meeting.",
            "recordingUrl": "http://example.com/recording.wav",
            "messages": [
                {"role": "user", "message": "Hello, I'd like to schedule a product consulting meeting.", "time": 1000},
                {"role": "bot", "message": "Of course! Let's check available slots tomorrow.", "time": 3000}
            ],
            "analysis": {
                "sentiment": "positive",
                "leadScore": 75
            }
        }
