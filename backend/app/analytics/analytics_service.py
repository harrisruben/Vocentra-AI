from app.core.logger import logger

class AnalyticsService:
    @staticmethod
    def record_metrics(
        call_sid: str,
        latency: float,
        tokens_used: int,
        tool_execution_time: float = 0.0,
        errors_count: int = 0
    ) -> None:
        # Outputs a structured string prefix to make ingestion by logs/metrics exporters easy
        logger.info(
            f"[TELEMETRY] CallSid: {call_sid} | latency={latency:.3f}s | "
            f"tokens={tokens_used} | tool_execution={tool_execution_time:.3f}s | "
            f"errors={errors_count}"
        )
